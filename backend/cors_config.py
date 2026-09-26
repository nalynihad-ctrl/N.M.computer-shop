"""Stage 2 - strong CORS security for the Naly,munib API.

This module is the single place where the CORS policy is defined. It is
deliberately strict:

1. NO WILDCARDS.  ``Access-Control-Allow-Origin: *`` is never produced, and a
   wildcard found in the environment is treated as a fatal misconfiguration
   rather than being silently honoured.
2. EXACT ORIGIN MATCHING.  Only the origins listed in the environment are
   accepted.  Substring/regex/suffix matching is not used, so
   ``https://evil-example.com`` can never match ``https://example.com``.
3. LEAST PRIVILEGE.  Only the HTTP methods and request headers the API really
   uses are advertised, and CORS headers are only attached to ``/api/*`` -
   never to the SPA HTML, static assets or ``/uploads/*`` images.
4. FAIL CLOSED.  If the policy cannot be proven safe (missing/invalid
   configuration in production) the process refuses to start instead of
   degrading into an open policy.
5. CREDENTIALS ARE OFF.  The frontend authenticates with a ``Bearer`` token
   (see ``frontend/src/api.js``), not cookies, so cookie credentials are never
   needed.  Even if they are switched on, the guard in :func:`build_policy`
   refuses any configuration that could combine credentials with a wildcard.
"""

from urllib.parse import urlsplit

from flask_cors import CORS

# --------------------------------------------------------------------------
# API surface
# --------------------------------------------------------------------------
# The API exposes read endpoints and a small number of write endpoints. There
# are no PUT/PATCH/DELETE routes, so those are never advertised.
CORS_METHODS = ["GET", "POST", "OPTIONS"]

# Exactly the request headers the frontend sends:
#   Content-Type: application/json  (JSON POST bodies)
#   Authorization: Bearer <token>   (Stage 1 token auth)
# OPTIONS is added by the CORS layer itself for preflight responses.
CORS_ALLOW_HEADERS = ["Authorization", "Content-Type"]

# No response header needs to be readable by browser JavaScript, so
# Access-Control-Expose-Headers is intentionally left empty.
CORS_EXPOSE_HEADERS = []

# Preflight results are cacheable for 10 minutes to avoid a round trip per
# non-simple request. This leaks no data.
CORS_MAX_AGE = 600

# Development-only fallbacks, used when DEV_ALLOWED_ORIGINS is not set. These
# are localhost URLs for the Vite dev server (5173) and `vite preview` (4173);
# no production host is referenced here.
DEV_DEFAULT_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
]

_TRUE_VALUES = {"1", "true", "yes", "on"}


def is_truthy(value):
    """Interpret a permissive boolean environment variable."""
    return str(value or "").strip().lower() in _TRUE_VALUES


class CorsConfigError(RuntimeError):
    """Raised when the CORS policy is missing or insecure. Always fatal."""


def _canonical_origin(raw):
    """Normalise one origin to the exact form a browser sends in ``Origin``.

    Browsers emit ``scheme://host[:port]`` with a lower-cased scheme and host
    and without a trailing slash, so the configuration is normalised the same
    way to keep comparisons exact.
    """
    if raw is None:
        raise CorsConfigError("Empty CORS origin entry.")

    value = str(raw).strip().strip('"').strip("'").strip()
    if not value:
        raise CorsConfigError("Empty CORS origin entry.")

    # A wildcard (or a wildcard-looking value) is never acceptable.
    if value == "*" or "*" in value:
        raise CorsConfigError(
            "Wildcard origin %r is forbidden. List every trusted origin "
            "explicitly, e.g. ALLOWED_ORIGINS=https://example.com,https://www.example.com"
            % value
        )

    parts = urlsplit(value)
    if parts.scheme.lower() not in ("http", "https"):
        # This also rejects the "null" origin used by sandboxed iframes and
        # local files, which must never be trusted for an authenticated API.
        raise CorsConfigError(
            "Origin %r must start with http:// or https:// (got scheme %r)."
            % (value, parts.scheme or "<none>")
        )
    if not parts.netloc:
        raise CorsConfigError("Origin %r is missing a host." % value)
    if parts.path not in ("", "/") or parts.query or parts.fragment:
        raise CorsConfigError(
            "Origin %r must not contain a path, query or fragment. Use the "
            "bare origin, e.g. https://example.com" % value
        )
    if "@" in parts.netloc:
        raise CorsConfigError("Origin %r must not contain credentials." % value)

    scheme = parts.scheme.lower()
    netloc = parts.netloc.lower()
    # Browsers omit the default port, so compare without it to avoid a
    # silent mismatch between https://x.com and https://x.com:443.
    if scheme == "https" and netloc.endswith(":443"):
        netloc = netloc[: -len(":443")]
    elif scheme == "http" and netloc.endswith(":80"):
        netloc = netloc[: -len(":80")]

    return "%s://%s" % (scheme, netloc)


def parse_origins(raw, *, source):
    """Parse a comma-separated origin list into canonical, de-duplicated origins."""
    if raw is None:
        return []
    origins, seen = [], set()
    for chunk in str(raw).split(","):
        if not chunk.strip():
            continue
        origin = _canonical_origin(chunk)
        if origin not in seen:
            seen.add(origin)
            origins.append(origin)
    if not origins:
        raise CorsConfigError("%s is set but contains no usable origin." % source)
    return origins


def build_policy(app_env, allowed_origins, dev_allowed_origins, supports_credentials):
    """Build the effective policy for the current environment.

    ``production`` reads ALLOWED_ORIGINS only and fails closed when it is
    missing or invalid. ``development`` reads DEV_ALLOWED_ORIGINS only, so
    production origins are never implicitly trusted while developing, and
    falls back to localhost dev-server origins.
    """
    env = (app_env or "development").strip().lower()
    if env not in ("development", "production"):
        raise CorsConfigError(
            "APP_ENV must be 'development' or 'production' (got %r)." % app_env
        )

    if env == "production":
        if not (allowed_origins or "").strip():
            # Fail safe: refuse to boot rather than default to "allow all".
            raise CorsConfigError(
                "ALLOWED_ORIGINS is required when APP_ENV=production. Set it to "
                "an explicit comma-separated list of trusted frontend origins, "
                "e.g. ALLOWED_ORIGINS=https://example.com,https://www.example.com"
            )
        origins = parse_origins(allowed_origins, source="ALLOWED_ORIGINS")
    else:
        # Development is intentionally isolated from the production allowlist.
        if (dev_allowed_origins or "").strip():
            origins = parse_origins(dev_allowed_origins, source="DEV_ALLOWED_ORIGINS")
        else:
            origins = list(DEV_DEFAULT_ORIGINS)

    # Defence in depth: credentials + wildcard can never be combined. The
    # parser already rejects wildcards, so this guards future edits.
    if supports_credentials and any(o == "*" for o in origins):
        raise CorsConfigError(
            "CORS credentials cannot be combined with a wildcard origin."
        )

    return {
        "env": env,
        "origins": origins,
        "methods": list(CORS_METHODS),
        "allow_headers": list(CORS_ALLOW_HEADERS),
        "expose_headers": list(CORS_EXPOSE_HEADERS),
        "supports_credentials": bool(supports_credentials),
        "max_age": CORS_MAX_AGE,
        "resources": {r"/api/*": {"origins": origins}},
    }


def init_cors(app, policy):
    """Attach the strict CORS policy to the Flask application.

    ``send_wildcard`` is disabled so an unrecognised origin receives no
    ``Access-Control-Allow-Origin`` header at all, and ``vary_header`` stays
    on so shared caches cannot serve one origin's response to another.
    """
    CORS(
        app,
        resources=policy["resources"],
        methods=policy["methods"],
        allow_headers=policy["allow_headers"],
        expose_headers=policy["expose_headers"],
        supports_credentials=policy["supports_credentials"],
        max_age=policy["max_age"],
        send_wildcard=False,
        vary_header=True,
    )
    return app


def verify_cors_policy(app, policy):
    """Startup self-check: prove the policy behaves as configured.

    Raises ``CorsConfigError`` if an allowed origin is not echoed back, or if
    an untrusted origin receives CORS headers it should never get. This turns
    a silent misconfiguration into a startup failure.
    """
    allowed = policy["origins"][0]
    blocked = "https://cors-unauthorized-origin.invalid"
    checks = (
        ("allowed origin", allowed, True),
        ("unauthorized origin", blocked, False),
    )
    with app.test_client() as client:
        for label, origin, should_have_header in checks:
            res = client.options(
                "/api/health",
                headers={
                    "Origin": origin,
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "authorization,content-type",
                },
            )
            echoed = res.headers.get("Access-Control-Allow-Origin")
            if should_have_header and echoed != origin:
                raise CorsConfigError(
                    "CORS self-check failed: allowed origin %r was not accepted "
                    "(got %r)." % (origin, echoed)
                )
            if not should_have_header and echoed is not None:
                raise CorsConfigError(
                    "CORS self-check failed: unauthorized origin %r received "
                    "Access-Control-Allow-Origin: %r." % (origin, echoed)
                )
    return True


def describe(policy):
    """Human-readable summary for the startup log (no secrets involved)."""
    return (
        "CORS[%s] origins=%s methods=%s allow_headers=%s credentials=%s"
        % (
            policy["env"],
            ",".join(policy["origins"]),
            ",".join(policy["methods"]),
            ",".join(policy["allow_headers"]),
            "on" if policy["supports_credentials"] else "off",
        )
    )
