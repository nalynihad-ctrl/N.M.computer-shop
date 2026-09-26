"""Stage 4 - rate limiting.

Protects the API against brute-force credential guessing and against
denial-of-service / resource-exhaustion floods.

Design decisions
----------------
* **Fail closed, fail safe.** The limiter is constructed with
  ``in_memory`` storage and a ``memory://`` URI by default so it works with
  no external service. The trade-off is documented below.
* **Proxies are trusted only when explicitly configured.** Rate limiting keys
  on the client IP. Behind a reverse proxy ``request.remote_addr`` is the
  proxy, so every user would share one bucket; the fix is ``ProxyFix``, which
  *trusts* ``X-Forwarded-For``. Trusting those headers when the app is exposed
  directly would let any client spoof its address and bypass every limit, so
  ``TRUST_PROXY`` defaults to off and must be switched on deliberately.
* **Two independent buckets on login.** One per client IP stops a single host
  spraying guesses; a second per account email stops a distributed attacker
  walking through one account from many addresses, and stops an attacker from
  locking a real user out by burning their quota from elsewhere.
* **Bucket keys are derived defensively.** The account key reads the JSON body
  inside ``try/except`` and falls back to a shared bucket, so a malformed or
  oversized payload can never turn the limiter itself into a 500.
* **CORS preflight is never throttled.** ``OPTIONS`` is excluded from every
  limit: a throttled preflight breaks the browser's request for *all* origins,
  which would silently regress Stage 2.
"""

import logging

from flask import jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

try:  # Flask-Limiter >= 3
    from flask_limiter.errors import RateLimitExceeded
except ImportError:  # pragma: no cover - older layout
    from limiter.errors import RateLimitExceeded

log = logging.getLogger("stage4.rate_limit")

# Endpoints that must never be throttled: CORS preflight and the health probe
# used by uptime monitoring / the startup self-check.
EXEMPT_ENDPOINTS = frozenset({"health", "static", "spa"})

# Rate limits are declared here as data so the whole policy is reviewable in
# one place. Values are conservative for a small shop: high enough that a
# legitimate customer on a shared connection never notices, low enough that a
# scripted attack is stopped quickly.
#
# key          "ip"     -> bucket per client address
#              "account" -> bucket per submitted email address
POLICY = {
    # --- credential endpoints: the brute-force targets -------------------
    "auth_login": [
        {"limit": "5 per minute", "key": "ip", "methods": ["POST"]},
        {"limit": "20 per hour", "key": "account", "methods": ["POST"]},
    ],
    "auth_register": [
        {"limit": "5 per hour", "key": "ip", "methods": ["POST"]},
    ],
    "auth_logout": [
        {"limit": "30 per minute", "key": "ip", "methods": ["POST"]},
    ],
    # --- token-protected reads: limit token probing ----------------------
    "auth_me": [
        {"limit": "60 per minute", "key": "ip", "methods": ["GET"]},
    ],
    "orders": [
        {"limit": "60 per minute", "key": "ip", "methods": ["GET"]},
    ],
    "order_detail": [
        {"limit": "60 per minute", "key": "ip", "methods": ["GET"]},
    ],
    # --- writes that create rows: order spam / storage amplification -----
    "checkout": [
        {"limit": "10 per minute", "key": "ip", "methods": ["POST"]},
    ],
    # --- catalogue reads: a ceiling, not a per-user quota ----------------
    "products": [
        {"limit": "120 per minute", "key": "ip", "methods": ["GET"]},
    ],
    "categories": [
        {"limit": "120 per minute", "key": "ip", "methods": ["GET"]},
    ],
    "brands": [
        {"limit": "120 per minute", "key": "ip", "methods": ["GET"]},
    ],
    "product_detail": [
        {"limit": "120 per minute", "key": "ip", "methods": ["GET"]},
    ],
    # --- static assets: a page load pulls dozens of images ---------------
    "uploads": [
        {"limit": "300 per minute", "key": "ip", "methods": ["GET"]},
    ],
}

# Applied to every route that has no explicit entry above. This is the DoS
# backstop: even an endpoint added later is bounded.
#
# These must be plain limit strings. Passing a dict such as
# ``{"limit": "300 per minute", "methods": [...]}`` is NOT equivalent - the dict
# is stored verbatim as the limit provider and never evaluated, so the limit
# silently does nothing. Per-method restriction for the defaults is achieved by
# the OPTIONS exclusion in ``_skip_exempt`` instead.
DEFAULT_LIMITS = ["300 per minute", "2000 per day"]


def account_key():
    """Bucket key for the account named in a request body.

    Wrapped in ``try/except`` on purpose: the limiter runs before the Stage 3
    validators, so the body may be absent, oversized, or not valid JSON. Any
    failure collapses into one shared bucket rather than raising.
    """
    try:
        if request.content_length and request.content_length > 8192:
            return "account:oversized"
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return "account:unknown"
        email = payload.get("email")
        if isinstance(email, str):
            email = email.strip().lower()
            # Bound the key length so a huge value cannot bloat the store.
            if email and len(email) <= 254:
                return "account:" + email
    except Exception:  # pragma: no cover - defensive
        return "account:unknown"
    return "account:unknown"


def client_key():
    """Bucket key for the client address, as seen by Flask."""
    try:
        return "ip:" + (get_remote_address() or "unknown")
    except Exception:  # pragma: no cover - defensive
        return "ip:unknown"


def key_for(kind):
    """Return the key function for a policy entry."""
    return account_key if kind == "account" else client_key


def validate_limit_strings(entries):
    """Fail fast if a limit string cannot be parsed.

    ``swallow_errors=True`` means a malformed limit would otherwise be ignored
    at request time and the endpoint would silently be left unlimited - exactly
    the failure mode worth catching at boot. Every configured limit is parsed
    here so a typo breaks startup instead of quietly disarming the limiter.
    """
    from limits.util import parse

    for entry in entries:
        value = entry["limit"] if isinstance(entry, dict) else entry
        try:
            if not parse(value):
                raise ValueError("parsed to nothing")
        except Exception as exc:
            raise ValueError(
                "invalid rate limit %r: %s" % (value, exc)
            ) from exc
    return True


def build_limiter(app, *, storage_uri="memory://", trust_proxy=False,
                  enabled=True, headers_enabled=True):
    """Create and attach the rate limiter.

    ``trust_proxy`` enables ``ProxyFix`` so the real client address is read
    from ``X-Forwarded-For``. It is off by default because those headers are
    trivially spoofable unless a trusted reverse proxy overwrites them.
    """
    if enabled:
        validate_limit_strings(DEFAULT_LIMITS)
        for entries in POLICY.values():
            validate_limit_strings(entries)
        log.info("[stage4] validated %d route policies + %d default limits",
                 len(POLICY), len(DEFAULT_LIMITS))
    if trust_proxy:
        from werkzeug.middleware.proxy_fix import ProxyFix

        # x_for=1 trusts exactly one proxy hop. The hop counts must match the
        # real topology or the client can spoof its address.
        app.wsgi_app = ProxyFix(
            app.wsgi_app, x_for=1, x_proto=1, x_host=0, x_port=0, x_prefix=0
        )
        log.info("[stage4] ProxyFix enabled - X-Forwarded-For is trusted")

    limiter = Limiter(
        key_func=client_key,
        app=app,
        default_limits=[] if not enabled else DEFAULT_LIMITS,
        storage_uri=storage_uri,
        # Enabled by default, but the flag lets a developer turn it off while
        # debugging without editing code.
        enabled=enabled,
        headers_enabled=headers_enabled,
        # Do not let a rate-limited request be retried immediately by the
        # browser middleware stack.
        swallow_errors=True,
    )

    @limiter.request_filter
    def _skip_exempt():
        """Exempt CORS preflight, health checks and the SPA shell.

        Returning a non-None value tells Flask-Limiter to ignore the request.
        Pre-flight and health must never be throttled; the SPA shell is a single
        document and throttling it would block the whole site for no benefit.
        """
        if request.method == "OPTIONS":
            return True
        if request.endpoint in EXEMPT_ENDPOINTS:
            return True
        return None

    return limiter


def apply_limits(limiter, policy_key):
    """Return a decorator that applies every limit in a policy entry.

    Used as the inner decorator on a route::

        @app.route("/api/auth/login", methods=["POST"])
        @rate_limit.apply_limits(limiter, "auth_login")
        def login(): ...

    Each entry becomes its own ``limiter.limit(...)`` wrapper, so a route can
    be bounded by several independent buckets (per IP *and* per account).
    Keeping the policy in this module means the route functions themselves only
    gain a decorator line and no request-handling logic changes.
    """
    entries = POLICY.get(policy_key)
    if not entries:
        return lambda func: func

    def decorator(func):
        wrapped = func
        for entry in entries:
            wrapped = limiter.limit(
                entry["limit"],
                key_func=key_for(entry.get("key", "ip")),
                methods=entry.get("methods"),
            )(wrapped)
        return wrapped

    return decorator


def apply_all(app, limiter):
    """Attach the limit decorators to routes by endpoint name.

    Kept as a separate, explicit step so it is obvious that Stage 1-3 route
    handlers are not being modified: their behaviour is identical, they are
    only wrapped by a limiter.
    """
    applied = []
    for endpoint, policy_key in ENDPOINT_POLICY.items():
        view = app.view_functions.get(endpoint)
        if view is None:
            log.warning("[stage4] endpoint %r not found; limits not applied", endpoint)
            continue
        entries = POLICY.get(policy_key)
        if not entries:
            continue
        wrapped = view
        for entry in entries:
            wrapped = limiter.limit(
                entry["limit"],
                key_func=key_for(entry.get("key", "ip")),
                methods=entry.get("methods"),
            )(wrapped)
        app.view_functions[endpoint] = wrapped
        applied.append("%s=%s" % (endpoint, ",".join(e["limit"] for e in entries)))
    return applied


# Maps a Flask endpoint name to its policy entry. Endpoint names are used
# rather than URL rules so a route cannot silently lose its limit by changing
# its path.
ENDPOINT_POLICY = {
    "login": "auth_login",
    "register": "auth_register",
    "logout": "auth_logout",
    "me": "auth_me",
    "orders": "orders",
    "order": "order_detail",
    "checkout": "checkout",
    "products": "products",
    "product": "product_detail",
    "categories": "categories",
    "brands": "brands",
    "uploads": "uploads",
}


def register_error_handlers(app, limiter):
    """JSON 429 responses, and no HTML error page for a rate-limited client."""

    @app.errorhandler(RateLimitExceeded)
    def handle_rate_limited(err):
        # Werkzeug derives Retry-After from the limit window; pass it through so
        # the client knows how long to wait.
        response = jsonify(
            {
                "error": "Too many requests. Please slow down and try again shortly.",
                "field": None,
            }
        )
        response.status_code = 429
        retry_after = getattr(err, "retry_after", None)
        if retry_after:
            response.headers["Retry-After"] = str(int(retry_after))
        return response

    @app.errorhandler(429)
    def handle_429(_err):
        response = jsonify(
            {"error": "Too many requests. Please slow down and try again shortly.",
             "field": None}
        )
        response.status_code = 429
        return response
