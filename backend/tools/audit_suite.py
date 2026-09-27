"""Stage 5 - consolidated end-to-end security audit.

Covers every stage (1-4) plus the cross-stage interactions that only show up
when the controls are exercised together.

    python tools/audit_suite.py

Exits non-zero if any check fails. Self-cleaning: every fixture it creates is
removed and product stock is restored, so it is safe to re-run.
"""
import json
import os
import re
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db, limiter
import config
import cors_config
import i18n
import rate_limit
import security_headers
import validation as v

app.config["PROPAGATE_EXCEPTIONS"] = False
C = app.test_client()
ORIGIN = "http://localhost:5173"
EVIL = "https://attacker.example"

results = []
section = ""


def head(title):
    global section
    section = title
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def check(name, cond, detail=""):
    results.append((section, name, bool(cond), detail))
    print("  %-4s %s%s" % ("ok" if cond else "FAIL", name,
                           ("   <- got: %s" % (detail,)) if not cond else ""))


def hdr(resp, name):
    for k, v_ in resp.headers.items():
        if k.lower() == name.lower():
            return v_
    return None


def all_headers(resp, name):
    return [v_ for k, v_ in resp.headers.items() if k.lower() == name.lower()]


def jbody(resp):
    try:
        return resp.get_json()
    except Exception:
        return None


AUDIT_EMAIL = "audit5_%d@example.com" % os.getpid()
AUDIT_PASS = "Audit-Passw0rd!23"
# Every account this suite creates matches one of these prefixes, so a crashed
# or interrupted run can never poison the next one.
TEST_EMAIL_PREFIXES = ("audit5_", "journey5_", "other5_", "victim2@", "expired5_",
                       "noexp5_", "junk5_", "bf")


def purge_test_data():
    """Remove anything a previous run of this suite left behind."""
    like = [p + "%" for p in TEST_EMAIL_PREFIXES]
    where = " OR ".join(["email LIKE ?"] * len(like))
    rows = db.query("SELECT id FROM users WHERE " + where, like)
    ids = [r["id"] for r in rows]
    if ids:
        marks = ",".join("?" * len(ids))
        db.execute("DELETE FROM order_items WHERE order_id IN "
                   "(SELECT id FROM orders WHERE user_id IN (%s))" % marks, ids)
        db.execute("DELETE FROM orders WHERE user_id IN (%s)" % marks, ids)
        db.execute("DELETE FROM users WHERE id IN (%s)" % marks, ids)
    return len(ids)


def restore_stock():
    """Put product stock back the way seed_data defines it."""
    from seed_data import build_products
    n = 0
    for p in build_products():
        n += db.execute("UPDATE products SET stock = ? WHERE name = ? AND stock <> ?",
                        (p["stock"], p["name"], p["stock"]))
    return n


purge_test_data()


def mkuser(email, token=None, expires="2099-01-01 00:00:00"):
    uid = db.execute(
        "INSERT INTO users (name, email, password_hash, api_token, "
        "token_expires_at, created_at) VALUES (?,?,?,?,?,?)",
        ("Audit User", email, "x$" + "0" * 64, token, expires, "2026-01-01"))
    return uid


def cleanup():
    purge_test_data()
    restore_stock()


# ===========================================================================
head("STAGE 1 - Token authentication and expiration")
# ===========================================================================
limiter.reset()
r = C.post("/api/auth/register", json={"name": "Audit", "email": AUDIT_EMAIL,
                                       "password": AUDIT_PASS})
check("register returns 201 + token", r.status_code == 201 and
      bool(jbody(r).get("token")), "%s %s" % (r.status_code, r.get_data(as_text=True)[:80]))
tok = (jbody(r) or {}).get("token")
check("token is long and random-looking",
      isinstance(tok, str) and len(tok) >= 32, str(len(tok or "")))
check("register never returns the password hash",
      "password" not in r.get_data(as_text=True).lower() and
      "hash" not in r.get_data(as_text=True).lower())

r = C.get("/api/auth/me", headers={"Authorization": "Bearer " + tok})
check("me() accepts a valid token", r.status_code == 200, str(r.status_code))
check("me() returns no password material",
      "password" not in r.get_data(as_text=True).lower())

check("me() rejects no token", C.get("/api/auth/me").status_code == 401)
check("me() rejects a garbage token",
      C.get("/api/auth/me", headers={"Authorization": "Bearer nope"}).status_code == 401)
check("me() rejects an empty bearer",
      C.get("/api/auth/me", headers={"Authorization": "Bearer "}).status_code == 401)
check("me() rejects a non-Bearer scheme",
      C.get("/api/auth/me", headers={"Authorization": "Basic " + tok}).status_code == 401)

# Token rotation on re-login.
r = C.post("/api/auth/login", json={"email": AUDIT_EMAIL, "password": AUDIT_PASS})
tok2 = (jbody(r) or {}).get("token")
check("login succeeds with correct password", r.status_code == 200, str(r.status_code))
check("login rotates the token", tok2 and tok2 != tok)
check("the previous token is dead after rotation",
      C.get("/api/auth/me", headers={"Authorization": "Bearer " + tok}).status_code == 401)
check("the new token works",
      C.get("/api/auth/me", headers={"Authorization": "Bearer " + tok2}).status_code == 200)
check("wrong password is 401 not 400",
      C.post("/api/auth/login", json={"email": AUDIT_EMAIL,
                                      "password": "wrongpass"}).status_code == 401)
check("login error does not reveal whether the account exists",
      jbody(C.post("/api/auth/login", json={"email": "ghost@example.com",
                                            "password": "x" * 8})).get("error")
      == jbody(C.post("/api/auth/login", json={"email": AUDIT_EMAIL,
                                               "password": "x" * 8})).get("error"))

# Expiry handling.
expired_tok = "expired-token-audit"
mkuser("expired5_%d@example.com" % os.getpid(), expired_tok, "2000-01-01 00:00:00")
check("an expired token is rejected",
      C.get("/api/auth/me", headers={"Authorization": "Bearer " + expired_tok}).status_code == 401)
noexp_tok = "noexpiry-token-audit"
mkuser("noexp5_%d@example.com" % os.getpid(), noexp_tok, None)
check("a token with no expiry is treated as expired (fail closed)",
      C.get("/api/auth/me", headers={"Authorization": "Bearer " + noexp_tok}).status_code == 401)
junk_tok = "junkexpiry-token-audit"
mkuser("junk5_%d@example.com" % os.getpid(), junk_tok, "not-a-date")
check("an unparseable expiry is treated as expired",
      C.get("/api/auth/me", headers={"Authorization": "Bearer " + junk_tok}).status_code == 401)

r = C.post("/api/auth/logout", json={}, headers={"Authorization": "Bearer " + tok2})
check("logout succeeds", r.status_code == 200, str(r.status_code))
check("the token is dead after logout",
      C.get("/api/auth/me", headers={"Authorization": "Bearer " + tok2}).status_code == 401)
check("logout is idempotent for an anonymous caller",
      C.post("/api/auth/logout", json={}).status_code == 200)
check("password_hash is never exposed by any endpoint",
      "pbkdf2" not in C.get("/api/auth/me",
                            headers={"Authorization": "Bearer " + tok}).get_data(as_text=True))

# ===========================================================================
head("STAGE 2 - CORS policy")
# ===========================================================================
limiter.reset()
r = C.get("/api/categories", headers={"Origin": ORIGIN})
check("allowed origin is echoed exactly", hdr(r, "Access-Control-Allow-Origin") == ORIGIN,
      str(hdr(r, "Access-Control-Allow-Origin")))
r = C.get("/api/categories", headers={"Origin": EVIL})
check("untrusted origin gets NO allow-origin header",
      hdr(r, "Access-Control-Allow-Origin") is None, str(hdr(r, "Access-Control-Allow-Origin")))
# The response that actually varies by origin is the ALLOWED one - a shared
# cache must not hand "ACAO: shop" to a different origin, so that is where
# Vary: Origin has to be present.
r_allowed = C.get("/api/categories", headers={"Origin": ORIGIN})
check("Vary: Origin is present so caches cannot cross-serve origins",
      "Origin" in (hdr(r_allowed, "Vary") or ""), str(hdr(r_allowed, "Vary")))
check("credentials are not enabled",
      hdr(r, "Access-Control-Allow-Credentials") is None)
for origin in ["*", "null", "http://localhost:5173.evil.com",
               "https://localhost:5173", "http://evil.com/?x=1", "file://"]:
    rr = C.get("/api/categories", headers={"Origin": origin})
    check("origin %-32s rejected" % origin,
          hdr(rr, "Access-Control-Allow-Origin") is None,
          str(hdr(rr, "Access-Control-Allow-Origin")))
r = C.options("/api/auth/login", headers={"Origin": ORIGIN,
                                          "Access-Control-Request-Method": "POST",
                                          "Access-Control-Request-Headers": "authorization,content-type"})
check("preflight allows POST", "POST" in (hdr(r, "Access-Control-Allow-Methods") or ""))
check("preflight allows Authorization + Content-Type",
      all(h.lower() in (hdr(r, "Access-Control-Allow-Headers") or "").lower()
          for h in ("authorization", "content-type")))
check("preflight denies an untrusted origin",
      hdr(C.options("/api/auth/login", headers={"Origin": EVIL,
                                                "Access-Control-Request-Method": "POST"}),
          "Access-Control-Allow-Origin") is None)
check("CORS is not applied to the SPA document",
      hdr(C.get("/"), "Access-Control-Allow-Origin") is None)
check("CORS is not applied to /uploads assets",
      hdr(C.get("/uploads/logo.svg"), "Access-Control-Allow-Origin") is None)
check("no wildcard is ever produced",
      all(hdr(C.get("/api/categories", headers={"Origin": o}), "Access-Control-Allow-Origin") != "*"
          for o in (ORIGIN, EVIL, "*")))

# ===========================================================================
head("STAGE 3 - Input validation and injection prevention")
# ===========================================================================
limiter.reset()
SQLI = ["' OR '1'='1", "'; DROP TABLE users;--", "1 UNION SELECT * FROM users",
        "admin'--", "\\'; DELETE FROM products WHERE '1'='1", "%' OR 1=1--"]
for p in SQLI:
    r = C.get("/api/products", query_string={"search": p})
    ok = r.status_code in (200, 400)
    check("SQLi in ?search=%-32r handled" % p[:32], ok, str(r.status_code))
check("users table survived the SQLi attempts",
      db.query_one("SELECT COUNT(*) AS c FROM users")["c"] >= 1)
check("products table survived the SQLi attempts",
      db.query_one("SELECT COUNT(*) AS c FROM products")["c"] > 0)

r = C.get("/api/products", query_string={"sort": "price; DROP TABLE users"})
check("ORDER BY injection is rejected", r.status_code == 400, str(r.status_code))
r = C.get("/api/products", query_string={"limit": "10; DELETE FROM users"})
check("LIMIT injection is rejected", r.status_code == 400, str(r.status_code))
r = C.get("/api/products", query_string={"category": "' OR 1=1--"})
check("category injection is handled", r.status_code in (200, 400), str(r.status_code))

# LIKE metacharacters must be literal, not wildcards.
allp = C.get("/api/products").get_json()
n_all = len(allp)
n_pct = len(C.get("/api/products", query_string={"search": "%"}).get_json())
n_us = len(C.get("/api/products", query_string={"search": "_"}).get_json())
check("search='%' is escaped, not a wildcard", n_pct < n_all,
      "%%=%d vs all=%d" % (n_pct, n_all))
check("search='_' is escaped, not a wildcard", n_us < n_all,
      "_=%d vs all=%d" % (n_us, n_all))

# Type confusion must be a 400, never a 500.
# The limiter is cleared before each call: these checks are about validation
# semantics, and the 5/min brute-force limit would otherwise mask the result
# with a 429 on the sixth login body.
for payload in [{"email": {"a": 1}, "password": "x"},
                {"email": ["a@b.com"], "password": "x"},
                {"email": "a@b.com", "password": 12345},
                {"email": "a@b.com", "password": True},
                {"email": "a@b.com", "password": "x", "role": "admin"},
                {"email": "a@b.com", "password": "x", "isAdmin": True}]:
    limiter.reset()
    r = C.post("/api/auth/login", json=payload)
    check("login type-confusion/unknown-field -> 400/401, never 500",
          r.status_code in (400, 401), "%s %s" % (r.status_code, payload))
limiter.reset()
r = C.post("/api/auth/login", data="not json", content_type="application/json")
check("malformed JSON is 400 not 500", r.status_code == 400, str(r.status_code))
limiter.reset()
r = C.post("/api/auth/login", data="[1,2,3]", content_type="application/json")
check("a JSON array body is rejected", r.status_code == 400, str(r.status_code))
limiter.reset()
big = '{"email":"a@b.com","password":"' + "x" * 70000 + '"}'
r = C.post("/api/auth/login", data=big, content_type="application/json")
check("an oversized body is refused with 413", r.status_code == 413, str(r.status_code))

# XSS payloads must survive round-trip without becoming an execution sink.
XSS = (
    "<script>alert(1)</script>",
    "javascript:alert(1)",
    '"><img src=x onerror=alert(1)>',
    "data:text/html;base64,PHNjcmlwdD4=",
    "<svg/onload=alert(1)>",
    "jav\tascript:alert(1)",
)
for p in XSS:
    r = C.get("/api/products", query_string={"search": p})
    check("XSS payload in ?search is inert (%r)" % p[:26],
          r.status_code in (200, 400) and "alert(1)" not in
          (jbody(r) if isinstance(jbody(r), dict) else {}).get("error", ""),
          str(r.status_code))
check("safe_media_path blocks javascript: URLs",
      v.safe_media_path("javascript:alert(1)", fallback="/x.svg") == "/x.svg")
check("safe_media_path blocks data: URLs",
      v.safe_media_path("data:text/html,<script>", fallback="/x.svg") == "/x.svg")
check("safe_media_path blocks attribute breakout",
      v.safe_media_path('x" onerror="alert(1)', fallback="/x.svg") == "/x.svg")
check("safe_media_path still allows a normal /uploads path",
      v.safe_media_path("/uploads/logo.svg", fallback="/x.svg") == "/uploads/logo.svg")
check("safe_media_path still allows an https URL",
      v.safe_media_path("https://cdn.example/a.png", fallback="/x") == "https://cdn.example/a.png")

# Traversal on the uploads route.
for p in ["/uploads/../app.py", "/uploads/..%2fapp.py", "/uploads/....//app.py",
          "/uploads/%2e%2e%2fapp.py", "/uploads/sub/dir.svg"]:
    r = C.get(p)
    check("traversal %-28s blocked" % p, r.status_code in (400, 404), str(r.status_code))
r = C.get("/uploads/logo.svg")
check("legitimate upload still served", r.status_code == 200, str(r.status_code))

# Cart arithmetic must stay bounded.
r = C.post("/api/checkout", json={
    "fullName": "A", "phone": "+15551112222", "email": "a@b.com",
    "address": "x", "city": "y", "country": "z", "paymentMethod": "Card Payment",
    "items": [{"productId": 1, "quantity": 10 ** 9}]})
check("an absurd quantity is rejected, not honoured",
      r.status_code in (400, 413), str(r.status_code))
r = C.post("/api/checkout", json={
    "fullName": "A", "phone": "+15551112222", "email": "a@b.com",
    "address": "x", "city": "y", "country": "z",
    "items": [{"productId": 1, "quantity": 1, "price": 0.01}]})
check("an unknown checkout field is rejected", r.status_code == 400, str(r.status_code))

# Identifier allowlist in db.py.
from db import UnsafeIdentifierError
for bad in ["users; DROP TABLE users", "users--", "`users`", "us ers", "", "1users",
            "users'", 'users"']:
    try:
        db.identifier(bad)
        check("identifier allowlist rejects %r" % bad, False, "ACCEPTED")
    except UnsafeIdentifierError:
        check("identifier allowlist rejects %r" % bad, True)
    except Exception as e:
        check("identifier allowlist rejects %r" % bad, False, type(e).__name__)
check("identifier allowlist accepts a normal name",
      db.identifier("users") == "users")

# ===========================================================================
head("STAGE 4 - Rate limiting, headers, error handling")
# ===========================================================================
limiter.reset()
codes = []
for i in range(8):
    rr = C.post("/api/auth/login", json={"email": "bf%d@example.com" % i,
                                         "password": "guess%d" % i})
    codes.append(rr.status_code)
    if rr.status_code == 429:
        last = rr
check("login brute force is blocked", 429 in codes, str(codes))
check("the 6th attempt is the one refused", codes[:5] == [401] * 5 and codes[5] == 429,
      str(codes))
check("429 body is JSON with error+field",
      isinstance(jbody(last), dict) and "error" in jbody(last))
check("429 sends Retry-After (the one status where it belongs)",
      hdr(last, "Retry-After") is not None, "absent")
check("429 leaks nothing about the limiter internals",
      not re.search(r"(limits\.|traceback|\.py)", last.get_data(as_text=True), re.I))
check("429 is not HTML", "<html" not in last.get_data(as_text=True).lower())

pre = [C.options("/api/auth/login", headers={"Origin": ORIGIN,
                                             "Access-Control-Request-Method": "POST"}).status_code
       for _ in range(15)]
check("CORS preflight is never throttled", 429 not in pre, str(sorted(set(pre))))

limiter.reset()
flood = [C.get("/api/brands").status_code for _ in range(130)]
check("a flood is bounded", 429 in flood, str(sorted(set(flood))))
check("the flood is refused at request 121", flood[:120] == [200] * 120 and flood[120] == 429,
      "first 429 at #%d" % (flood.index(429) + 1 if 429 in flood else -1))

limiter.reset()
uncovered = [e for e in {r_.endpoint for r_ in app.url_map.iter_rules()}
             if e not in rate_limit.ENDPOINT_POLICY and e not in rate_limit.EXEMPT_ENDPOINTS]
check("no route is accidentally unlimited", not uncovered, str(uncovered))
check("all limit strings parse (validated at boot)",
      rate_limit.validate_limit_strings(rate_limit.DEFAULT_LIMITS))

# Headers
limiter.reset()
r = C.get("/api/categories", headers={"Origin": ORIGIN})
check("API: exactly one CSP header", len(all_headers(r, "Content-Security-Policy")) == 1)
check("API: CSP is default-src 'none' (Stage 3 intact)",
      "default-src 'none'" in hdr(r, "Content-Security-Policy"))
check("API: CSP not weakened by Stage 4",
      "unsafe-inline" not in hdr(r, "Content-Security-Policy") and
      "fonts.googleapis" not in hdr(r, "Content-Security-Policy"))
for h, want in [("X-Content-Type-Options", "nosniff"), ("X-Frame-Options", "DENY"),
                ("Referrer-Policy", "strict-origin-when-cross-origin"),
                ("X-XSS-Protection", "0")]:
    check("API: %s = %s" % (h, want), hdr(r, h) == want, str(hdr(r, h)))
check("API: Permissions-Policy denies camera/mic/geo",
      all(x in (hdr(r, "Permissions-Policy") or "") for x in
          ("camera=()", "microphone=()", "geolocation=()")))
check("no HSTS over plain HTTP", hdr(r, "Strict-Transport-Security") is None)
check("no Retry-After on a 200", hdr(r, "Retry-After") is None, str(hdr(r, "Retry-After")))
check("no Set-Cookie anywhere (no CSRF surface)",
      hdr(r, "Set-Cookie") is None and "password" not in r.get_data(as_text=True).lower())

r = C.get("/")
csp = hdr(r, "Content-Security-Policy") or ""
check("SPA: exactly one CSP header", len(all_headers(r, "Content-Security-Policy")) == 1)
check("SPA: allows its own script", "'self'" in csp)
check("SPA: allows the inline theme script", "unsafe-inline" in csp)
check("SPA: allows Google Fonts", "fonts.googleapis.com" in csp and "fonts.gstatic.com" in csp)
check("SPA: blocks inline event handlers", "script-src-attr 'none'" in csp)
check("SPA: blocks plugins/framing/base-hijack/form-exfil",
      all(x in csp for x in ("object-src 'none'", "frame-ancestors 'none'",
                             "base-uri 'self'", "form-action 'self'")))
check("SPA: third-party origins are NOT in script-src",
      not re.search(r"script-src[^;]*fonts\.", csp))
html = r.get_data(as_text=True)
check("SPA: served HTML really does contain an inline <script>",
      re.search(r"<script(?![^>]*\bsrc=)", html) is not None)
for ref in re.findall(r'(?:src|href)="(/[^"]+)"', html):
    rr = C.get(ref)
    check("asset %-34s loads" % ref, rr.status_code == 200, str(rr.status_code))
    check("  ...with the permissive CSP so the browser will run it",
          "default-src 'self'" in (hdr(rr, "Content-Security-Policy") or ""),
          str(hdr(rr, "Content-Security-Policy"))[:40])

# Error handling / no leakage
def boom():
    raise RuntimeError("SECRET hunter2 /var/secret.db line 42 app.py")


saved = app.view_functions["categories"]
app.view_functions["categories"] = boom
r = C.get("/api/categories", headers={"Origin": ORIGIN})
txt = r.get_data(as_text=True)
check("unhandled exception -> 500", r.status_code == 500, str(r.status_code))
check("500 is JSON", (hdr(r, "Content-Type") or "").startswith("application/json"))
check("500 hides the exception message", "hunter2" not in txt)
check("500 hides the traceback", "Traceback" not in txt)
check("500 hides file paths", "app.py" not in txt and "secret.db" not in txt)
check("500 hides the exception type", "RuntimeError" not in txt)
check("500 still carries an operator correlation id", bool((jbody(r) or {}).get("incident")))
check("500 still carries security headers", hdr(r, "X-Content-Type-Options") == "nosniff")
check("500 carries CORS for an allowed origin",
      hdr(r, "Access-Control-Allow-Origin") == ORIGIN)
app.view_functions["categories"] = saved

# ===========================================================================
head("STAGE 5 - CROSS-STAGE INTEGRATION (the important part)")
# ===========================================================================
limiter.reset()

# 1. Error responses must keep CORS + security headers, and must not gain CORS
#    for an untrusted origin. A browser cannot read a blocked error otherwise.
for label, mk in [
    ("400 validation", lambda: C.post("/api/auth/login", json={"email": "bad"})),
    ("401 auth", lambda: C.get("/api/orders")),
    ("404 unknown", lambda: C.get("/api/nope")),
    ("413 too large", lambda: C.post("/api/auth/login", data=big,
                                     content_type="application/json")),
]:
    r = mk()
    check("%-14s keeps nosniff" % label, hdr(r, "X-Content-Type-Options") == "nosniff")
    check("%-14s keeps CSP" % label, hdr(r, "Content-Security-Policy") is not None)
    check("%-14s is JSON" % label,
          (hdr(r, "Content-Type") or "").startswith("application/json"),
          str(hdr(r, "Content-Type")))
r = C.post("/api/auth/login", json={"email": "bad"}, headers={"Origin": EVIL})
check("error response gives an untrusted origin no CORS",
      hdr(r, "Access-Control-Allow-Origin") is None)

# 2. The limiter must not swallow auth/validation semantics.
limiter.reset()
r = C.get("/api/orders")
check("a protected route returns 401, not 429, when under the limit",
      r.status_code == 401, str(r.status_code))
r = C.post("/api/auth/login", json={"email": "bad"})
check("a validation failure returns 400, not 429",
      r.status_code == 400, str(r.status_code))

# 3. Stage 3 validation must win over Stage 4 account bucketing on a bad body.
limiter.reset()
r = C.post("/api/auth/login", data="{bad", content_type="application/json")
check("malformed login body still 400 (limiter key did not crash it)",
      r.status_code == 400, str(r.status_code))

# 4. Full authenticated journey end to end.
limiter.reset()
r = C.post("/api/auth/register", json={"name": "Journey",
                                       "email": "journey5_%d@example.com" % os.getpid(),
                                       "password": AUDIT_PASS})
jtok = (jbody(r) or {}).get("token")
check("journey: register", r.status_code == 201, str(r.status_code))
AUTH = {"Authorization": "Bearer " + jtok}
r = C.get("/api/auth/me", headers=AUTH)
check("journey: me", r.status_code == 200, str(r.status_code))
pid = C.get("/api/products", query_string={"limit": 1}).get_json()[0]["id"]
r = C.post("/api/checkout", json={
    "fullName": "Journey User", "phone": "+15551234567",
    "email": "journey5@example.com", "address": "5 Test St", "city": "Austin",
    "country": "United States", "paymentMethod": "Card Payment",
    "items": [{"productId": pid, "quantity": 1}]}, headers=AUTH)
check("journey: checkout", r.status_code == 201, "%s %s" % (r.status_code,
                                                            r.get_data(as_text=True)[:90]))
checkout_body = jbody(r) or {}
# A client that keys off the canonical status must get the same pair from the
# checkout response as from the order payloads, or it has to special-case its own
# request. The code is also what the stylesheet slug is derived from.
check("journey: checkout returns a canonical statusCode",
      checkout_body.get("statusCode") in i18n.ORDER_STATUSES,
      str(checkout_body.get("statusCode")))
check("journey: checkout status is the translation of that code",
      checkout_body.get("status") == i18n.order_status("en", checkout_body.get("statusCode")),
      "%r / %r" % (checkout_body.get("status"), checkout_body.get("statusCode")))
oid = checkout_body.get("orderId")

r = C.get("/api/orders", headers=AUTH)
check("journey: order list", r.status_code == 200, str(r.status_code))
check("journey: the new order is listed",
      any(o["id"] == oid for o in (jbody(r) or [])), str(oid))
r = C.get("/api/orders/%d" % oid, headers=AUTH)
check("journey: order detail for the owner", r.status_code == 200, str(r.status_code))

# 5. Broken access control (Stage 5 fix) - the audit's main finding.
check("AUTHZ: anonymous order read is refused",
      C.get("/api/orders/%d" % oid).status_code == 401)
other_tok = "other-journey-token-5"
mkuser("other5_%d@example.com" % os.getpid(), other_tok, "2099-01-01 00:00:00")
r = C.get("/api/orders/%d" % oid, headers={"Authorization": "Bearer " + other_tok})
check("AUTHZ: another user's order read is refused", r.status_code == 404, str(r.status_code))
check("AUTHZ: no PII leaks to another user",
      not any(k in (jbody(r) or {}) for k in ("fullName", "phone", "email", "address")))
check("AUTHZ: missing order and foreign order are indistinguishable",
      C.get("/api/orders/99999999", headers={"Authorization": "Bearer " + other_tok}).status_code
      == r.status_code)
check("AUTHZ: the owner can still read their own order",
      C.get("/api/orders/%d" % oid, headers=AUTH).status_code == 200)

# 6. Token must not be accepted from the query string (leaks into logs/referrers).
check("a token in the query string does NOT authenticate",
      C.get("/api/orders?token=" + jtok).status_code == 401)

# 7. CSRF surface: bearer tokens are not cookies, so cross-site form posts
#    cannot carry credentials.
check("no session cookie is ever set", "Set-Cookie" not in
      C.post("/api/auth/login",
             json={"email": AUDIT_EMAIL, "password": AUDIT_PASS}).headers)
check("credentials support is off in the policy",
      config.CORS_POLICY["supports_credentials"] is False)

# 8. Production posture.
check("no debug flag is enabled", app.debug is False)
check("the app does not propagate exceptions in production",
      app.config.get("PROPAGATE_EXCEPTIONS") in (None, False))
check("SECRET_KEY comes from the environment, not source",
      config.SECRET_KEY == os.environ.get("SECRET_KEY"))
check("TRUST_PROXY is off by default (X-Forwarded-For not blindly trusted)",
      config.TRUST_PROXY is False)
check("rate limiting is on", config.RATE_LIMIT_ENABLED is True)
check("body size cap is set", app.config["MAX_CONTENT_LENGTH"] == 64 * 1024)
check("HSTS preload is off by default", config.HSTS_PRELOAD is False)

# 9. Stage isolation: nothing from 1-3 was removed.
check("Stage 1 token TTL constant still present",
      getattr(__import__("app"), "TOKEN_TTL_DAYS", None) == 7)
check("Stage 2 CORS policy still built from env",
      config.CORS_POLICY["origins"] == cors_config.build_policy(
          config.APP_ENV, config.ALLOWED_ORIGINS, config.DEV_ALLOWED_ORIGINS,
          config.CORS_SUPPORTS_CREDENTIALS)["origins"])
check("Stage 3 identifier allowlist still exported", callable(db.identifier))
check("all four tables still exist",
      all(db.count(t) >= 0 for t in ("products", "users", "orders", "order_items")))

# ===========================================================================
head("PRODUCTION CORS FAIL-CLOSED (separate process)")
# ===========================================================================
import subprocess
env = dict(os.environ, APP_ENV="production")
env.pop("ALLOWED_ORIGINS", None)
p = subprocess.run([sys.executable, "-c", "import app"], env=env,
                   capture_output=True, text=True)
check("production with no ALLOWED_ORIGINS refuses to boot",
      p.returncode != 0 and "ALLOWED_ORIGINS is required" in (p.stderr + p.stdout),
      "rc=%s" % p.returncode)
env2 = dict(os.environ, APP_ENV="production", ALLOWED_ORIGINS="https://shop.example")
p2 = subprocess.run([sys.executable, "-c", "import app"], env=env2,
                    capture_output=True, text=True)
check("production with an exact origin boots", p2.returncode == 0,
      (p2.stderr or "")[-200:])
env3 = dict(os.environ, APP_ENV="production", ALLOWED_ORIGINS="*")
p3 = subprocess.run([sys.executable, "-c", "import app"], env=env3,
                    capture_output=True, text=True)
check("production with a wildcard origin refuses to boot",
      p3.returncode != 0 and "Wildcard origin" in (p3.stderr + p3.stdout),
      "rc=%s" % p3.returncode)

# ===========================================================================
cleanup()
limiter.reset()

failed = [r for r in results if not r[2]]
print()
print("=" * 72)
print("STAGE 5 AUDIT RESULT: %d passed, %d failed  (of %d checks)"
      % (len(results) - len(failed), len(failed), len(results)))
if failed:
    print()
    print("FAILURES")
    for sec, name, _, detail in failed:
        print("  [%s] %s   %s" % (sec.split(" - ")[0], name, detail))
print("=" * 72)
sys.exit(1 if failed else 0)
