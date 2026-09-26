"""Stage 3 - input validation and injection prevention.

Every value that arrives from a client (JSON body, query string, URL rule
variable, form field, file name) must pass through this module before it
reaches business logic or the database.

Design rules
------------
* **Validate, do not sanitise-by-silently-mutating.** A malformed value is
  rejected with HTTP 400 and a message that names the offending field without
  echoing the value back or revealing internals.
* **Fail on the wrong type.** ``"abc".strip()`` style code raises a 500 on a
  list/int payload; every cleaner type-checks first.
* **Length is bounded** on every string so a single request cannot exhaust
  memory, and so the password hash cannot be turned into a CPU-exhaustion
  payload.
* **Control characters are stripped** (C0/C1, zero-width, BOM, U+2028/9).
  This blocks null-byte truncation, log/terminal escape injection and
  Trojan-Source style homoglyph tricks. Text is NFKC-normalised first so
  fullwidth/compatibility look-alikes cannot bypass a format check.
* **XSS is handled by output context, not by mangling stored data.** The API
  returns ``application/json``, which browsers do not execute, and
  :func:`safe_media_path` blocks ``javascript:``/``data:`` URLs from reaching
  an ``<img src>``/``href`` sink. Free text is stored intact so the UI keeps
  rendering names like ``O'Brien & Sons`` correctly; React escapes it on
  render, and the response hardening in ``app.py`` (nosniff + CSP) is the
  backstop if some other client renders the JSON as HTML.
* **LIKE metacharacters are escaped** so a search term cannot widen the match
  (see :func:`escape_like`).
"""

import json
import re
import unicodedata

from flask import jsonify, request

# --------------------------------------------------------------------------
# Limits
# --------------------------------------------------------------------------
# Sized to the real UI: the longest seeded product description is well under
# these caps, so legitimate input is never rejected.
MAX_NAME = 80
MAX_EMAIL = 254          # RFC 5321 maximum path length
MAX_PASSWORD = 128       # bounds the PBKDF2 cost of a hostile payload
MIN_PASSWORD = 4         # unchanged from the original rule
MAX_PHONE = 32
MAX_ADDRESS = 200
MAX_CITY = 80
MAX_COUNTRY = 80
MAX_SEARCH = 100
MAX_CATEGORY = 60
MAX_BRAND = 60
MAX_BRANDS_PER_QUERY = 20   # caps the generated "IN (?, ?, ...)" clause
MAX_MEDIA_PATH = 255
MAX_PAYMENT_METHOD = 40

MAX_ID = 2147483647         # matches INTEGER PRIMARY KEY on both backends
MIN_PRICE = 0.0
MAX_PRICE = 1000000.0
MAX_QUANTITY_PER_ITEM = 99  # mirrors the cart cap in frontend CartContext
MAX_CART_ITEMS = 50
MAX_PAGE_SIZE = 200         # unchanged from the original LIMIT ceiling
MIN_PAGE_SIZE = 1

# Flask rejects oversized bodies with 413 before any handler runs.
MAX_CONTENT_LENGTH = 64 * 1024

# --------------------------------------------------------------------------
# Patterns
# --------------------------------------------------------------------------
# Control characters that must never reach the database: C0 except tab/newline/
# carriage return, DEL, C1, zero-width characters (Trojan Source / homoglyph
# smuggling), the Unicode line/paragraph separators and the BOM.
_CONTROL_RE = re.compile(
    "[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\u200b-\u200f\u2028\u2029\ufeff]"
)
_WHITESPACE_RUN_RE = re.compile(r"[^\S\n]+")   # horizontal whitespace runs
_NEWLINE_RUN_RE = re.compile(r"\n{3,}")
# [0-9] rather than \d: \d also matches Arabic-Indic and other Unicode digits,
# which would let a payload sneak past an "integer" check.
_INT_RE = re.compile(r"^[+-]?[0-9]{1,19}$")
_DECIMAL_RE = re.compile(r"^[+-]?(?:[0-9]{1,15}(?:\.[0-9]{1,6})?|\.[0-9]{1,6})$")

_EMAIL_RE = re.compile(
    r"^[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+"
    r"(?:\.[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+)*"
    r"@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$"
)
_PHONE_RE = re.compile(r"^[0-9+()\-.\s]{6,32}$")
# Only a same-origin /uploads/ path or an absolute http(s) URL is acceptable.
_MEDIA_PATH_RE = re.compile(r"^(?:/uploads/[A-Za-z0-9._-]{1,200}|https?://[^\s]{1,255})$")
_FILENAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")

# Sort keys are a fixed allowlist mapped to fixed SQL fragments in app.py, so a
# caller can never inject an ORDER BY clause.
SORT_VALUES = ("popular", "newest", "price_asc", "price_desc", "name")
# The two methods the checkout UI offers.
PAYMENT_METHODS = ("Cash on Delivery", "Card Payment")

# "!" is used as the LIKE escape character rather than "\" because a backslash
# literal is not portable across the SQLite and MySQL dialects this app speaks.
LIKE_ESCAPE_CHAR = "!"

_UNSAFE_MEDIA_CHARS = re.compile(r"[\s\"'<>`\\\x00-\x1f\x7f]")


class ValidationError(ValueError):
    """A client supplied an invalid value. Rendered as HTTP 400."""

    def __init__(self, field, message, code="invalid"):
        super().__init__(message)
        self.field = field
        self.message = message
        self.code = code

    def to_response(self):
        # The message is a fixed sentence chosen by this module; the offending
        # value is never echoed back, so nothing user-controlled is reflected.
        return jsonify({"error": self.message, "field": self.field}), 400


# --------------------------------------------------------------------------
# Primitives
# --------------------------------------------------------------------------
def require_str(value, field):
    """Accept only a real string. bool/int/float/list/dict are all rejected."""
    if isinstance(value, str):
        return value
    raise ValidationError(field, "Field '%s' must be a string." % field)


def clean_text(
    value,
    field,
    *,
    required=True,
    min_len=1,
    max_len=MAX_NAME,
    multiline=False,
    pattern=None,
    pattern_message=None,
):
    """Normalise and bound a free-text field.

    Order matters: type check, then NFKC, then control-character strip, then
    whitespace collapse, then length. Doing length last means a payload cannot
    pad itself past the cap with ignorable characters.
    """
    # ``request.args.get(...)`` yields None for an absent query parameter, and
    # ``data.get(...)`` yields None for an absent JSON key. None is treated as
    # "not supplied" so `required=False` fields work; a present-but-wrong-typed
    # value is still rejected below.
    raw = "" if value is None else require_str(value, field)

    # NFKC folds fullwidth/compatibility forms (ｅ.g. U+FF33) back to ASCII so
    # they cannot masquerade as a valid value downstream.
    cleaned = unicodedata.normalize("NFKC", raw)
    cleaned = _CONTROL_RE.sub(" ", cleaned)

    if multiline:
        lines = [_WHITESPACE_RUN_RE.sub(" ", ln).strip() for ln in cleaned.split("\n")]
        cleaned = _NEWLINE_RUN_RE.sub("\n\n", "\n".join(lines)).strip()
    else:
        cleaned = _WHITESPACE_RUN_RE.sub(" ", cleaned.replace("\n", " ")).strip()

    if not cleaned:
        if required:
            raise ValidationError(field, "Field '%s' is required." % field)
        return ""

    # Length is counted in characters after normalisation.
    if len(cleaned) < min_len:
        raise ValidationError(
            field, "Field '%s' must be at least %d characters." % (field, min_len)
        )
    if len(cleaned) > max_len:
        raise ValidationError(
            field, "Field '%s' must be at most %d characters." % (field, max_len)
        )
    if pattern is not None and not pattern.match(cleaned):
        raise ValidationError(
            field, pattern_message or "Field '%s' has an invalid format." % field
        )
    return cleaned


def clean_email(value, field="email", *, required=True):
    """Validate an email address and normalise it to lower case."""
    cleaned = clean_text(
        value, field, required=required, min_len=3, max_len=MAX_EMAIL
    )
    if not cleaned:
        return ""
    lowered = cleaned.lower()
    if not _EMAIL_RE.match(lowered):
        raise ValidationError(field, "Field '%s' must be a valid email address." % field)
    return lowered


def clean_phone(value, field="phone", *, required=True):
    """Validate a phone number: digits plus the usual separators only.

    The character class is an allowlist, so angle brackets, quotes and
    semicolons cannot reach storage, and the length cap stops an oversized
    value being used to bloat a row.
    """
    cleaned = clean_text(
        value, field, required=required, min_len=6, max_len=MAX_PHONE
    )
    if not cleaned:
        return ""
    if not _PHONE_RE.match(cleaned):
        raise ValidationError(field, "Field '%s' must be a valid phone number." % field)
    return cleaned


def clean_password(value, field="password", *, required=True, min_len=MIN_PASSWORD):
    """Validate a password.

    Passwords are deliberately NOT trimmed, NFKC-normalised or stripped of
    characters: every character is significant and altering it would break
    existing credentials. Only type, emptiness and length are checked. The
    upper bound matters because hashing is deliberately expensive.
    """
    if value is None:
        value = ""
    if isinstance(value, bool) or not isinstance(value, str):
        raise ValidationError(field, "Field '%s' must be a string." % field)
    if not value:
        if required:
            raise ValidationError(field, "Field '%s' is required." % field)
        return ""
    if len(value) < min_len:
        raise ValidationError(
            field, "Password must be at least %d characters." % min_len
        )
    if len(value) > MAX_PASSWORD:
        raise ValidationError(
            field, "Password must be at most %d characters." % MAX_PASSWORD
        )
    return value


def clean_int(
    value,
    field,
    *,
    minimum=None,
    maximum=None,
    required=True,
    default=None,
):
    """Parse a bounded integer. Rejects floats with a fraction, NaN and '1e5'."""
    if value is None or (isinstance(value, str) and not value.strip()):
        if required:
            raise ValidationError(field, "Field '%s' is required." % field)
        return default
    if isinstance(value, bool):
        raise ValidationError(field, "Field '%s' must be an integer." % field)
    if isinstance(value, int):
        parsed = value
    elif isinstance(value, float):
        if value != int(value):
            raise ValidationError(field, "Field '%s' must be a whole number." % field)
        parsed = int(value)
    elif isinstance(value, str):
        text = value.strip()
        if not _INT_RE.match(text):
            raise ValidationError(field, "Field '%s' must be an integer." % field)
        parsed = int(text)
    else:
        raise ValidationError(field, "Field '%s' must be an integer." % field)

    if minimum is not None and parsed < minimum:
        raise ValidationError(
            field, "Field '%s' must be greater than or equal to %s." % (field, minimum)
        )
    if maximum is not None and parsed > maximum:
        raise ValidationError(
            field, "Field '%s' must be less than or equal to %s." % (field, maximum)
        )
    return parsed


def clean_number(
    value,
    field,
    *,
    minimum=None,
    maximum=None,
    required=True,
    default=None,
):
    """Parse a bounded decimal.

    A strict regex is used instead of ``float()`` because ``float()`` happily
    accepts ``nan``/``inf``, which would silently poison comparisons and the
    ``min``/``max`` clamps.
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        if required:
            raise ValidationError(field, "Field '%s' is required." % field)
        return default
    if isinstance(value, bool):
        raise ValidationError(field, "Field '%s' must be a number." % field)
    if isinstance(value, (int, float)):
        parsed = float(value)
        if parsed != parsed or parsed in (float("inf"), float("-inf")):
            raise ValidationError(field, "Field '%s' must be a finite number." % field)
    elif isinstance(value, str):
        text = value.strip()
        if not _DECIMAL_RE.match(text):
            raise ValidationError(field, "Field '%s' must be a number." % field)
        parsed = float(text)
    else:
        raise ValidationError(field, "Field '%s' must be a number." % field)

    if minimum is not None and parsed < minimum:
        raise ValidationError(
            field, "Field '%s' must be greater than or equal to %s." % (field, _num(minimum))
        )
    if maximum is not None and parsed > maximum:
        raise ValidationError(
            field, "Field '%s' must be less than or equal to %s." % (field, _num(maximum))
        )
    return parsed


def _num(value):
    """Render a bound without a trailing '.0' so messages read naturally."""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def clean_choice(value, field, choices, *, default=None, required=False):
    """Accept only one of a fixed set of values (allowlist, never a pattern)."""
    if value is None or (isinstance(value, str) and not value.strip()):
        if required:
            raise ValidationError(field, "Field '%s' is required." % field)
        return default
    text = require_str(value, field).strip()
    if text not in choices:
        raise ValidationError(
            field,
            "Field '%s' must be one of: %s." % (field, ", ".join(choices)),
        )
    return text


def clean_bool(value, field, *, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ("true", "1", "yes", "on"):
            return True
        if lowered in ("false", "0", "no", "off", ""):
            return False
    raise ValidationError(field, "Field '%s' must be a boolean." % field)


# --------------------------------------------------------------------------
# XSS / output-context helpers
# --------------------------------------------------------------------------
def safe_media_path(value, field="image", *, required=False, fallback=None):
    """Validate a media path or URL before it can reach an ``src``/``href``.

    This is the sink that actually matters for XSS in a JSON API: a stored
    ``javascript:alert(1)`` in an image field becomes script execution the
    moment a client puts it in an anchor's ``href``. Only a same-origin
    ``/uploads/...`` path or an absolute ``http(s)`` URL is accepted, and
    characters that would break out of an HTML attribute are rejected outright.
    """
    if value is None:
        if required:
            raise ValidationError(field, "Field '%s' is required." % field)
        return fallback or ""
    raw = require_str(value, field)
    candidate = unicodedata.normalize("NFKC", raw).strip()
    if not candidate:
        if required:
            raise ValidationError(field, "Field '%s' is required." % field)
        return fallback or ""
    if _UNSAFE_MEDIA_CHARS.search(candidate) or not _MEDIA_PATH_RE.match(candidate):
        # Fall back to a known-good asset instead of echoing an unsafe value.
        return fallback or ""
    if len(candidate) > MAX_MEDIA_PATH:
        return fallback or ""
    return candidate


def escape_like(term, escape_char=LIKE_ESCAPE_CHAR):
    """Escape LIKE metacharacters so a search term cannot widen the match.

    Without this, ``search=%`` matches every row and ``search=_`` matches any
    single character. The escaped pattern must be used with an explicit
    ``ESCAPE`` clause; ``app.py`` adds ``ESCAPE '!'``.
    """
    if term is None:
        return None
    return (
        term.replace(escape_char, escape_char * 2)
        .replace("%", escape_char + "%")
        .replace("_", escape_char + "_")
    )


def escape_html(value):
    """Escape text for an HTML context.

    Not needed for the JSON API itself (``jsonify`` emits
    ``application/json``, which is inert, and React escapes on render), but
    provided for any future HTML/email rendering of stored values.
    """
    from markupsafe import escape  # imported lazily; Werkzeug always ships it

    return str(escape(value or ""))


# --------------------------------------------------------------------------
# Request-level guards
# --------------------------------------------------------------------------
def json_object(*, required=True):
    """Return the request body as a dict, or raise a clean 400/415.

    Enforces the JSON content type, rejects a body that is not a JSON object,
    and distinguishes "empty body" from "malformed JSON" so the caller gets an
    accurate message. An array or scalar body is rejected because every
    endpoint here expects named fields.
    """
    content_type = (request.content_type or "").split(";")[0].strip().lower()
    if content_type and content_type != "application/json":
        raise ValidationError(
            "Content-Type",
            "Content-Type must be application/json.",
            code="unsupported_media_type",
        )
    raw = request.get_data(cache=True, as_text=False)
    if not raw or not raw.strip():
        if required:
            raise ValidationError("body", "A JSON request body is required.")
        return {}
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        raise ValidationError("body", "Request body must be valid JSON.")
    if not isinstance(parsed, dict):
        raise ValidationError("body", "Request body must be a JSON object.")
    return parsed


def reject_unknown_fields(data, allowed, *, context="body"):
    """Reject any field that is not part of the documented contract.

    Unknown fields are usually a sign of a malformed or hostile request; they
    are also a mass-assignment risk if a future handler starts binding request
    data straight onto a model.
    """
    if not isinstance(data, dict):
        raise ValidationError(context, "Request body must be a JSON object.")
    unexpected = sorted(set(data) - set(allowed))
    if unexpected:
        raise ValidationError(
            unexpected[0],
            "Unexpected field%s: %s."
            % ("" if len(unexpected) == 1 else "s", ", ".join(unexpected)),
        )
    return data


def clean_filename(value, field="filename"):
    """Validate a file name used for a static asset lookup.

    ``send_from_directory`` already blocks traversal, but rejecting separators,
    dot-segments and control characters here means a malicious name is refused
    with a 400 instead of being quietly normalised.
    """
    raw = clean_text(
        value, field, required=True, min_len=1, max_len=128, multiline=False
    )
    if not _FILENAME_RE.match(raw) or ".." in raw:
        raise ValidationError(field, "Field '%s' is not a valid file name." % field)
    return raw


def csv_list(value, field, *, max_items, max_item_len):
    """Validate a comma-separated query parameter into a bounded list."""
    raw = clean_text(
        value,
        field,
        required=False,
        min_len=1,
        max_len=max_items * (max_item_len + 1) + 1,
    )
    if not raw:
        return []
    parts = [p.strip() for p in raw.split(",")]
    parts = [p for p in parts if p]
    if not parts:
        return []
    if len(parts) > max_items:
        raise ValidationError(
            field, "Field '%s' accepts at most %d values." % (field, max_items)
        )
    out = []
    for part in parts:
        if len(part) > max_item_len:
            raise ValidationError(
                field,
                "Each value in '%s' must be at most %d characters."
                % (field, max_item_len),
            )
        out.append(part)
    return out
