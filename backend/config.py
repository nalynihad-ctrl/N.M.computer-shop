import os
from dotenv import load_dotenv

import cors_config

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# --- MySQL configuration ---------------------------------------------------
# Override any of these with environment variables before starting the server.
MYSQL_CONFIG = {
    "host": os.environ.get("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.environ.get("MYSQL_PORT", "3306")),
    "user": os.environ.get("MYSQL_USER", "root"),
    "password": os.environ.get("MYSQL_PASSWORD", ""),
    "charset": "utf8mb4",
}

MYSQL_DATABASE = os.environ.get("MYSQL_DB", "computer_shop")

# --- SQLite fallback -------------------------------------------------------
# Used automatically when MySQL is not reachable (or PyMySQL is not installed).
SQLITE_PATH = os.path.join(BASE_DIR, "data", "computer_shop.db")

UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")
FRONTEND_DIST = os.path.normpath(os.path.join(BASE_DIR, "..", "frontend", "dist"))

SECRET_KEY = os.environ.get("SECRET_KEY", "my_computer_shopppp_secret_710910810")

# --- CORS (Stage 2: strong CORS security) -----------------------------------
# Nothing below is a secret and nothing is hard-coded: the trusted frontend
# origins are read from the environment. `cors_config` validates them and
# raises CorsConfigError (fatal) if the policy would be unsafe, so importing
# this module is already the startup validation.
#
# APP_ENV              "development" (default) or "production".
# ALLOWED_ORIGINS      production only, REQUIRED when APP_ENV=production.
#                      Comma-separated, exact origins. Wildcards are rejected.
#                      e.g. ALLOWED_ORIGINS=https://example.com,https://www.example.com
# DEV_ALLOWED_ORIGINS  development only. Defaults to the local Vite dev/preview
#                      servers, so production origins are never trusted while
#                      developing.
APP_ENV = os.environ.get("APP_ENV", "development")
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "")
DEV_ALLOWED_ORIGINS = os.environ.get("DEV_ALLOWED_ORIGINS", "")

# The frontend authenticates with `Authorization: Bearer <token>` (see
# frontend/src/api.js), never with cookies, so CORS credentials stay OFF.
# Turning this on is safe: the policy can only contain exact origins, never a
# wildcard, and credentials + wildcard is rejected outright.
CORS_SUPPORTS_CREDENTIALS = cors_config.is_truthy(
    os.environ.get("CORS_SUPPORTS_CREDENTIALS", "false")
)

# Methods/headers/credentials are fixed in cors_config to the minimum the API
# needs; only the origin allowlist comes from the environment.
CORS_POLICY = cors_config.build_policy(
    APP_ENV, ALLOWED_ORIGINS, DEV_ALLOWED_ORIGINS, CORS_SUPPORTS_CREDENTIALS
)
CORS_ORIGINS = CORS_POLICY["origins"]
CORS_METHODS = CORS_POLICY["methods"]
CORS_ALLOW_HEADERS = CORS_POLICY["allow_headers"]

# --- Stage 4: rate limiting -------------------------------------------------
# The per-route limits themselves live in rate_limit.POLICY so the whole policy
# is reviewable in one place. Only the operational switches are configurable.
#
# RATE_LIMIT_ENABLED     set false to disable limiting while debugging locally.
# RATE_LIMIT_STORAGE_URI where counters live. The default "memory://" is
#                        per-process and resets on restart; use a shared backend
#                        such as "redis://host:6379/0" when running more than
#                        one worker, otherwise each worker keeps its own count.
# TRUST_PROXY            trust X-Forwarded-For so the real client IP is used.
#                        Leave false unless a reverse proxy you control
#                        overwrites that header, otherwise a client can spoof
#                        its address and bypass every limit.
RATE_LIMIT_ENABLED = cors_config.is_truthy(
    os.environ.get("RATE_LIMIT_ENABLED", "true")
)
RATE_LIMIT_STORAGE_URI = os.environ.get("RATE_LIMIT_STORAGE_URI", "memory://")
TRUST_PROXY = cors_config.is_truthy(os.environ.get("TRUST_PROXY", "false"))

# --- Stage 4: security headers ----------------------------------------------
# Third-party origins the HTML document may load fonts/styles from. This must
# match what frontend/index.html references; it is added only to style-src and
# font-src, never to script-src, so a compromised CDN still cannot run code.
CSP_ALLOWED_EXTERNAL_ORIGINS = [
    o.strip()
    for o in os.environ.get(
        "CSP_ALLOWED_EXTERNAL_ORIGINS",
        "https://fonts.googleapis.com https://fonts.gstatic.com",
    ).split()
    if o.strip()
]
# includeSubDomains pins every subdomain of the site to HTTPS. Only enable it
# once every subdomain actually serves HTTPS.
HSTS_INCLUDE_SUBDOMAINS = cors_config.is_truthy(
    os.environ.get("HSTS_INCLUDE_SUBDOMAINS", "true")
)
# preload is a one-way trip: it submits the domain to browser vendors' HSTS
# preload list, which is very hard to undo. Off by default.
HSTS_PRELOAD = cors_config.is_truthy(os.environ.get("HSTS_PRELOAD", "false"))

# Shipping / discount rules used by checkout
FREE_SHIPPING_THRESHOLD = 100.0
SHIPPING_FLAT_RATE = 9.99
