"""Stage 4 - HTTP security response headers.

Stage 3 already added ``nosniff``, ``X-Frame-Options``, ``Referrer-Policy``
and ``X-XSS-Protection`` plus a locked-down ``default-src 'none'`` CSP for
``/api/*`` responses. Those are left exactly as they are; this module adds the
remaining headers and must never weaken what is already there.

What is added here
------------------
* ``Strict-Transport-Security`` - only meaningful over HTTPS, and only emitted
  when the request actually arrived over TLS (or a trusted proxy says it did).
  Sending it over plain HTTP would be ignored by browsers anyway, while
  sending it wrongly can pin a hostname to HTTPS for a long time.
* ``Permissions-Policy`` - switches off browser features the shop has no use
  for (camera, microphone, geolocation, payment), reducing the surface if the
  React app is ever compromised.
* ``Content-Security-Policy`` for the **HTML** responses (the SPA shell).

CSP and the single-page app
---------------------------
A blanket ``default-src 'none'`` would be right for JSON but would **break the
site**, because ``frontend/index.html`` (and the built ``dist/index.html``)
legitimately contains:

* an inline ``<script>`` that restores the saved light/dark theme before
  first paint, and
* Google Fonts loaded from ``https://fonts.googleapis.com`` (CSS) and
  ``https://fonts.gstatic.com`` (font files).

So the document policy keeps same-origin scripts and those two font origins
while removing what actually causes harm: third-party script hosts, inline
event handlers (``script-src-attr 'none'`` - the real XSS execution vector),
plugins, framing, ``<base>`` hijacking and form exfiltration.

If the frontend later drops the inline theme script and self-hosts its fonts,
``'unsafe-inline'`` can be removed from ``script-src``/``style-src`` and the
policy tightened further; that is a frontend change, tracked in the comment on
``CSP_SCRIPT_SRC`` below.
"""

from flask import request

# Sent on every response. Keeping the feature list empty means "deny all",
# which is the safest default for an e-commerce site.
DEFAULT_PERMISSIONS_POLICY = (
    "accelerometer=(), autoplay=(), camera=(), display-capture=(), "
    "encrypted-media=(), fullscreen=(self), geolocation=(), gyroscope=(), "
    "magnetometer=(), microphone=(), midi=(), payment=(), picture-in-picture=(), "
    "publickey-credentials-get=(), screen-wake-lock=(), sync-xhr=(), usb=(), "
    "xr-spatial-tracking=()"
)

# Two years is the value recommended for HSTS preload eligibility. Only applied
# to HTTPS responses.
HSTS_MAX_AGE = 31536000


def build_api_csp():
    """Locked-down policy for JSON endpoints.

    Identical in effect to the Stage 3 policy; it is defined here so this module
    is self-documenting, and it is deliberately NOT applied by this module (see
    ``apply_headers``) so Stage 3 remains the single authority for API CSP.
    """
    return "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"


def build_document_csp(extra_origins=(), script_src=None, style_src=None,
                       font_src=None, secure=False):
    """Policy for the HTML document served to the browser.

    ``extra_origins`` are third-party origins the document legitimately loads
    from (currently Google Fonts). It is supplied by configuration rather than
    hard-coded so it can be changed without touching this module, and it is
    only ever added to ``style-src``/``font-src`` - never to ``script-src``,
    so a compromised font CDN still cannot inject JavaScript.
    """
    origins = [o for o in (extra_origins or ()) if o]
    directives = [
        "default-src 'self'",
        "base-uri 'self'",
        "object-src 'none'",
        "frame-ancestors 'none'",
        "frame-src 'none'",
        "form-action 'self'",
        "manifest-src 'self'",
        "connect-src 'self'",
        "img-src 'self' data:",
        # Inline event handlers (onerror=, onclick=) are the practical XSS
        # execution path; React uses addEventListener, not inline handlers, so
        # this costs the app nothing.
        "script-src-attr 'none'",
        "script-src %s" % (script_src or "'self' 'unsafe-inline'"),
        "style-src %s" % (
            style_src or " ".join(["'self'", "'unsafe-inline'"] + origins)
        ),
        "font-src %s" % (font_src or " ".join(["'self'"] + origins)),
    ]
    if secure:
        # Ask the browser to rewrite any http:// sub-resource to https://.
        directives.append("upgrade-insecure-requests")
    return "; ".join(directives)


def build_hsts(max_age=HSTS_MAX_AGE, include_subdomains=True, preload=False):
    value = "max-age=%d" % max_age
    if include_subdomains:
        value += "; includeSubDomains"
    if preload:
        value += "; preload"
    return value


def request_is_secure(trust_proxy):
    """True when the client reached us over TLS.

    Without a trusted proxy in front, ``request.is_secure`` reflects the real
    connection scheme. A header can only be believed when ``trust_proxy`` is
    on, otherwise any client could claim HTTPS and make us emit HSTS.
    """
    try:
        if request.is_secure:
            return True
        if trust_proxy:
            return (request.headers.get("X-Forwarded-Proto", "") or "").lower() == "https"
    except Exception:  # pragma: no cover - defensive
        return False
    return False


def strip_misplaced_retry_after(response):
    """Keep ``Retry-After`` only on the status codes where it is meaningful.

    Flask-Limiter's header injection adds ``Retry-After`` to *every* response it
    evaluates, including ``200``, ``400``, ``401`` and ``413``. RFC 9110 10.2.3
    defines that header for ``3xx`` and ``503`` only, so on a ``200`` it is
    non-conformant. It is not merely cosmetic: a shared cache or CDN that
    honours it can delay revalidation of a perfectly good response, and the
    value discloses when the current rate-limit window rolls over.

    The ``429`` is left alone because that is exactly where the header belongs;
    :func:`rate_limit.register_error_handlers` also sets it there.

    ORDERING IS LOAD-BEARING. Flask runs ``after_request`` callbacks in reverse
    registration order, so this must be registered *before* the limiter (and
    before the Stage 3/Stage 4 header hooks) in order to run *last* and see the
    limiter's output. The call site in ``app.py`` is deliberately near the top
    of the file for that reason - do not move it down.
    """
    if response.status_code != 429 and "Retry-After" in response.headers:
        del response.headers["Retry-After"]
    return response


def apply_headers(response, *, extra_origins=(), hsts_max_age=HSTS_MAX_AGE,
                  hsts_include_subdomains=True, hsts_preload=False,
                  trust_proxy=False):
    """Add the Stage 4 headers to a response.

    Only ``setdefault`` is used and the document CSP is skipped on ``/api/*``,
    so the Stage 3 API policy can never be overwritten or duplicated by this
    function.
    """
    secure = request_is_secure(trust_proxy)

    # Permissions-Policy is meaningful over both HTTP and HTTPS.
    response.headers.setdefault("Permissions-Policy", DEFAULT_PERMISSIONS_POLICY)

    # HSTS: only over TLS, where the browser will actually honour it.
    if secure:
        response.headers.setdefault(
            "Strict-Transport-Security",
            build_hsts(hsts_max_age, hsts_include_subdomains, hsts_preload),
        )

    # Document CSP for the SPA shell. Stage 3 already sets a stricter
    # ``default-src 'none'`` on /api/*, so it is deliberately left alone.
    if not request.path.startswith("/api/"):
        response.headers.setdefault(
            "Content-Security-Policy",
            build_document_csp(extra_origins=extra_origins, secure=secure),
        )
    return response
