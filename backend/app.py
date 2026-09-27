"""Naly,munib backend.

Run:  python app.py
The Flask server exposes a REST API under /api and serves the built React
frontend from ../frontend/dist when available.
"""

import json
import os
import secrets
import hashlib
from datetime import datetime, timedelta, timezone

from flask import Flask, Response, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge

import config
import cors_config
import i18n
import rate_limit
import security_headers
import validation as v
from db import Database
from seed_data import CATEGORY_META, build_products

app = Flask(__name__)

# --------------------------------------------------------------------------
# Localisation
# --------------------------------------------------------------------------
def lang():
    """The language for this request: ``?lang=``, else Accept-Language, else en.

    Resolved per request rather than held in module state so that a single
    process can serve all three languages without any session state.
    """
    return i18n.current_language()


def api_error(message, status=400, field=None, **extra):
    """Build a localised JSON error body.

    The English sentence stays the key, so a message with no translation falls
    through unchanged and the English response is byte-identical to before.
    """
    payload = {"error": i18n.error_message(lang(), message), "field": field}
    payload.update(extra)
    return jsonify(payload), status


# --------------------------------------------------------------------------
# Stage 3 - input validation limits
# --------------------------------------------------------------------------
# Oversized bodies are refused with 413 by Flask before any handler runs, so a
# single request cannot be used to exhaust memory.
app.config["MAX_CONTENT_LENGTH"] = v.MAX_CONTENT_LENGTH

# --------------------------------------------------------------------------
# Stage 5 - header conformance cleanup
# --------------------------------------------------------------------------
# Registered FIRST on purpose. Flask runs after_request callbacks in reverse
# registration order, so a hook registered here executes LAST - after the
# rate limiter, after the Stage 4 header hook and after the Stage 3 hook. It
# therefore sees, and can correct, the final header set rather than being
# overwritten by it. Do not move this block further down the file.
app.after_request(security_headers.strip_misplaced_retry_after)

# --------------------------------------------------------------------------
# Stage 2 - CORS security
# --------------------------------------------------------------------------
# The trusted origins come from ALLOWED_ORIGINS / DEV_ALLOWED_ORIGINS in .env
# and were already validated while `config` was imported. `build_policy` in
# cors_config.py is what refuses to boot on a missing, wildcard or otherwise
# insecure configuration when APP_ENV=production, so the server can never fall
# back to `Access-Control-Allow-Origin: *`.
# CORS uses `after_request`, so it must be attached before the first request
# is handled; the live self-check runs at the bottom of this file, once every
# route exists.
cors_config.init_cors(app, config.CORS_POLICY)

app.config["JSON_SORT_KEYS"] = False

# --------------------------------------------------------------------------
# Stage 3 - centralised error handling and response hardening
# --------------------------------------------------------------------------
@app.errorhandler(v.ValidationError)
def handle_validation_error(err):
    """Turn a rejected field into a clean 400 with no internals leaked."""
    response, status = err.to_response()
    # Localising here rather than in validation.py keeps that module free of any
    # request/transport concern, and the body is rebuilt from the parsed JSON
    # rather than from a raw string, so nothing is re-serialised by hand.
    body = response.get_json() or {}
    body["error"] = i18n.validation_message(lang(), body.get("error"))
    return jsonify(body), status


@app.errorhandler(RequestEntityTooLarge)
def handle_too_large(_err):
    return api_error("Request body is too large.", 413, field="body")


@app.errorhandler(HTTPException)
def handle_http_exception(err):
    """Return JSON for framework-level errors on the API.

    Without this, a 404/405/415 on /api/* would render Werkzeug's HTML error
    page, which is both the wrong content type for an API client and an extra
    surface for markup injection.
    """
    if not request.path.startswith("/api/"):
        return err
    return api_error(err.name, err.code or 500)


@app.after_request
def harden_api_response(response):
    """Defence-in-depth headers for every API response.

    * ``nosniff`` stops a browser from re-interpreting a JSON body as HTML,
      which is what would otherwise turn reflected JSON into XSS.
    * A locked-down ``default-src 'none'`` CSP means that even if some client
      renders the payload as markup, no script can execute or load.
    * ``frame-ancestors 'none'`` stops clickjacking; the SPA is same-origin
      only and must not be framed.
    * ``X-XSS-Protection: 0`` disables the legacy auditor, which can itself
      introduce XSS.

    No ``Access-Control-*`` header is set here, so Stage 2's CORS policy
    remains the single source of truth for cross-origin behaviour.
    """
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("X-XSS-Protection", "0")
    if request.path.startswith("/api/"):
        response.headers.setdefault(
            "Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'"
        )
    return response


# --------------------------------------------------------------------------
# Stage 4 - safe error handling
# --------------------------------------------------------------------------
@app.errorhandler(Exception)
def handle_unexpected_error(err):
    """Last-resort handler: log the detail, return none of it.

    Anything not already handled by a more specific handler lands here. The
    exception object is *never* rendered into the response - no message, no
    type name, no traceback, no request body - because those routinely contain
    SQL fragments, file paths, hostnames and library versions. The full detail
    goes to the server log, where only an operator with log access can read it.

    The response carries a random correlation id so an operator can find the
    matching stack trace in the log without the client learning anything about
    the internals.
    """
    incident_id = secrets.token_hex(8)
    app.logger.error(
        "[incident:%s] unhandled %s on %s %s",
        incident_id,
        type(err).__name__,
        request.method,
        request.path,
        exc_info=True,
    )
    if request.path.startswith("/api/"):
        return api_error("Internal Server Error", 500, incident=incident_id)
    return (
        Response(
            "Internal Server Error",
            status=500,
            mimetype="text/plain",
        ),
        500,
    )


# --------------------------------------------------------------------------
# Stage 4 - rate limiting
# --------------------------------------------------------------------------
# Built before the routes exist; the per-endpoint limits are attached at the
# bottom of this file, once every view function is registered.
limiter = rate_limit.build_limiter(
    app,
    storage_uri=config.RATE_LIMIT_STORAGE_URI,
    trust_proxy=config.TRUST_PROXY,
    enabled=config.RATE_LIMIT_ENABLED,
)
# A rate-limited client gets JSON with Retry-After, never Flask-Limiter's
# default HTML page.
rate_limit.register_error_handlers(app, limiter)


# --------------------------------------------------------------------------
# Stage 4 - additional security headers
# --------------------------------------------------------------------------
@app.after_request
def add_stage4_headers(response):
    """Layer the Stage 4 headers on top of the Stage 3 ones.

    ``setdefault`` plus the ``/api/*`` guard mean this cannot duplicate or
    weaken the stricter CSP that Stage 3 already applies to API responses.
    """
    return security_headers.apply_headers(
        response,
        extra_origins=config.CSP_ALLOWED_EXTERNAL_ORIGINS,
        hsts_include_subdomains=config.HSTS_INCLUDE_SUBDOMAINS,
        hsts_preload=config.HSTS_PRELOAD,
        trust_proxy=config.TRUST_PROXY,
    )


db = Database(config.MYSQL_CONFIG, config.MYSQL_DATABASE, config.SQLITE_PATH)
db.init_schema()

# Lifetime of an API token, counted from the moment it is issued.
TOKEN_TTL_DAYS = 7

# --------------------------------------------------------------------------
# Seeding
# --------------------------------------------------------------------------
def seed_if_empty():
    if db.count("products") == 0:
        now = datetime.utcnow()
        rows = []
        for p in build_products():
            rows.append(
                (
                    p["name"], p["brand"], p["category"], p["description"],
                    p["price"], p["old_price"], p["discount"], p["image"],
                    p["images"], p["stock"], p["rating"], p["specs"],
                    (now - timedelta(days=p["days_ago"])).isoformat(sep=" "),
                )
            )
        db.execute_many(
            """INSERT INTO products
               (name, brand, category, description, price, old_price, discount,
                image, images, stock, rating, specs, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            rows,
        )
        print("[seed] inserted %d sample products" % len(rows))

seed_if_empty()

# Migration: rename the "Mice" category to "Mouse" in existing databases.
db.execute("UPDATE products SET category = ? WHERE category = ?", ("Mouse", "Mice"))


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def parse_json_field(value, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def product_dict(row, language=i18n.DEFAULT_LANGUAGE):
    # Stage 3 - output encoding for URL-typed fields. The frontend drops this
    # value straight into `<img src={product.image} />`, so a stored
    # `javascript:` or `data:` URL would be an XSS sink. safe_media_path allows
    # only the `/uploads/...` form the catalogue actually uses and silently
    # falls back to a known-good asset otherwise, so no legitimate product is
    # affected.
    image = v.safe_media_path(
        row["image"], "image", fallback="/uploads/accessories.svg"
    )
    name, description = i18n.product_text(
        language, row["name"], row["description"]
    )
    return {
        "id": int(row["id"]),
        "name": name,
        "brand": row["brand"],
        # `category` stays the canonical English key so that the /category/...
        # route, the ?category= filter and the cart keep working in any
        # language; `categoryName` is the label to actually render.
        "category": row["category"],
        "categoryName": i18n.category_name(language, row["category"]),
        "description": description,
        "price": round(float(row["price"]), 2),
        "oldPrice": round(float(row["old_price"] or 0), 2),
        "discount": int(row["discount"] or 0),
        "image": image,
        "images": [
            v.safe_media_path(p, "images", fallback=image) or image
            for p in parse_json_field(row["images"], [row["image"]])
        ],
        "stock": int(row["stock"] or 0),
        "rating": float(row["rating"] or 0),
        "specs": i18n.localize_specs(
            language, parse_json_field(row["specs"], {})
        ),
        "createdAt": row["created_at"],
    }


def user_dict(row):
    if not row:
        return None
    return {
        "id": int(row["id"]),
        "name": row["name"],
        "email": row["email"],
        "phone": row.get("phone", ""),
        "address": row.get("address", ""),
        "city": row.get("city", ""),
        "country": row.get("country", ""),
    }


def hash_password(password):
    salt = secrets.token_hex(8)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
    return "%s$%s" % (salt, digest)


def verify_password(password, stored):
    try:
        salt, digest = stored.split("$")
    except ValueError:
        return False
    test = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
    return secrets.compare_digest(test, digest)


def bearer_token():
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:].strip()
    return None


def new_token_expiry():
    """ISO-8601 UTC timestamp for a freshly issued token."""
    expires = datetime.now(timezone.utc) + timedelta(days=TOKEN_TTL_DAYS)
    return expires.replace(microsecond=0).isoformat()


def parse_token_expiry(value):
    """Parse a stored expiry into a timezone-aware UTC datetime, or None."""
    if not value:
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        text = str(value).strip()
        if not text:
            return None
        if text.endswith(("Z", "z")):
            text = text[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            parsed = None
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
                try:
                    parsed = datetime.strptime(text, fmt)
                    break
                except ValueError:
                    continue
            if parsed is None:
                return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def token_is_valid(row):
    """A token is valid only when it has a present, parseable, unexpired expiry.

    A missing or malformed ``token_expires_at`` is treated as expired so that
    tokens issued before expiry existed can never stay valid forever.
    """
    if not row:
        return False
    expires = parse_token_expiry(row.get("token_expires_at"))
    if expires is None:
        return False
    return expires > datetime.now(timezone.utc)


def current_user():
    token = bearer_token()
    if not token:
        return None
    row = db.query_one("SELECT * FROM users WHERE api_token = ?", (token,))
    if not token_is_valid(row):
        return None
    return row


# --------------------------------------------------------------------------
# API: catalogue
# --------------------------------------------------------------------------
@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "database": db.backend_name, "time": datetime.utcnow().isoformat()})


@app.route("/api/categories")
def categories():
    rows = db.query(
        """SELECT category, COUNT(*) AS product_count, MIN(price) AS min_price,
                  MAX(price) AS max_price
           FROM products GROUP BY category ORDER BY category"""
    )
    language = lang()
    out = []
    for r in rows:
        out.append(
            {
                # `name` is the label to render, so it follows the request
                # language; `key` is the stable English value the client sends
                # back as ?category= and puts in the /category/... route.
                "name": i18n.category_name(language, r["category"]),
                "key": r["category"],
                "productCount": int(r["product_count"]),
                "image": "/uploads/" + CATEGORY_META.get(r["category"], "accessories.svg"),
                "minPrice": round(float(r["min_price"]), 2),
                "maxPrice": round(float(r["max_price"]), 2),
            }
        )
    return jsonify(out)


@app.route("/api/brands")
def brands():
    rows = db.query("SELECT DISTINCT brand FROM products ORDER BY brand")
    return jsonify([r["brand"] for r in rows])


@app.route("/api/products")
def products():
    # --- Stage 3: every query parameter is type-checked and length-bounded ---
    category = v.clean_text(
        request.args.get("category"), "category",
        required=False, max_len=v.MAX_CATEGORY,
    )
    brand_values = v.csv_list(
        request.args.get("brand"), "brand",
        max_items=v.MAX_BRANDS_PER_QUERY, max_item_len=v.MAX_BRAND,
    )
    search = v.clean_text(
        request.args.get("search"), "search",
        required=False, max_len=v.MAX_SEARCH,
    )
    # An allowlist, not a pattern: `sort` selects a fixed SQL fragment from
    # `order_map`, so a caller can never inject an ORDER BY clause.
    sort = v.clean_choice(
        request.args.get("sort"), "sort", v.SORT_VALUES, default="popular"
    )
    min_price = v.clean_number(
        request.args.get("minPrice"), "minPrice",
        required=False, minimum=v.MIN_PRICE, maximum=v.MAX_PRICE, default=None,
    )
    max_price = v.clean_number(
        request.args.get("maxPrice"), "maxPrice",
        required=False, minimum=v.MIN_PRICE, maximum=v.MAX_PRICE, default=None,
    )
    limit = v.clean_int(
        request.args.get("limit"), "limit",
        required=False, minimum=v.MIN_PAGE_SIZE, maximum=v.MAX_PAGE_SIZE,
        default=None,
    )
    # The cart holds product ids, not localized names, so it asks for its lines
    # back by id whenever the language changes. Without this a cart built in one
    # language would keep showing the other language's product names, because the
    # stored snapshot is a copy of whichever language happened to be active when
    # the item was added.
    ids = v.csv_int_list(
        request.args.get("ids"), "ids",
        max_items=v.MAX_CART_ITEMS,
    )
    if min_price is not None and max_price is not None and min_price > max_price:
        return api_error("minPrice cannot be greater than maxPrice.")

    language = lang()

    # --- Stage 3: WHERE values are always bound with `?` placeholders -------
    where, params = [], []
    if ids:
        # `ids` is already a bounded list of validated integers, so the
        # placeholder count comes from the list and every value is bound.
        where.append("id IN (%s)" % ",".join("?" * len(ids)))
        params.extend(ids)
    if category:
        # Always the canonical English key, never a localized label, so the
        # filter keeps working and stays shareable.
        where.append("category = ?")
        params.append(category)
    if brand_values:
        # The number of placeholders comes from the validated list length, never
        # from the raw text, and each brand is still bound as a parameter.
        where.append("brand IN (%s)" % ",".join("?" * len(brand_values)))
        params.extend(brand_values)
    if search:
        # The SQL LIKE runs against the English columns, so a shopper typing an
        # Arabic or Kurdish word would match nothing. When that happens the
        # translated text is searched instead and its matches narrow the query.
        # Only one of the two branches adds a WHERE clause, never both: the
        # localized pass must be able to find rows the English LIKE misses, and
        # the English pass is the fallback so an English term still works
        # while a non-English language is selected.
        localized_ids = []
        if language != i18n.DEFAULT_LANGUAGE:
            localized_ids = i18n.localized_matches(language, db.query(
                "SELECT id, name, brand, category, description, specs FROM products"
            ), search)
        if localized_ids:
            where.append("id IN (%s)" % ",".join("?" * len(localized_ids)))
            params.extend(localized_ids)
        else:
            # LIKE metacharacters are escaped and the pattern is bound, so a
            # search term is matched literally instead of widening the query.
            like = "%" + v.escape_like(search.lower()) + "%"
            where.append(
                "(LOWER(name) LIKE ? ESCAPE '!' OR LOWER(brand) LIKE ? ESCAPE '!' "
                "OR LOWER(category) LIKE ? ESCAPE '!' "
                "OR LOWER(description) LIKE ? ESCAPE '!' "
                "OR LOWER(specs) LIKE ? ESCAPE '!')"
            )
            params.extend([like] * 5)
    if min_price is not None:
        where.append("price >= ?")
        params.append(min_price)
    if max_price is not None:
        where.append("price <= ?")
        params.append(max_price)

    order_map = {
        "price_asc": "price ASC",
        "price_desc": "price DESC",
        "newest": "created_at DESC",
        "popular": "rating DESC, stock DESC",
        "name": "name ASC",
    }
    # `sort` came from the allowlist, so this lookup always hits a literal.
    order_by = order_map[sort]

    sql = "SELECT * FROM products"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY " + order_by
    if limit is not None:
        # LIMIT is bound as a parameter too. Both backends accept a placeholder
        # here, so no integer is ever formatted into the statement.
        sql += " LIMIT ?"
        params.append(limit)

    rows = db.query(sql, params)
    return jsonify([product_dict(r, language) for r in rows])


@app.route("/api/products/<int:product_id>")
def product(product_id):
    row = db.query_one("SELECT * FROM products WHERE id = ?", (product_id,))
    if not row:
        return api_error("Product not found", 404)
    return jsonify(product_dict(row, lang()))


# --------------------------------------------------------------------------
# API: auth
# --------------------------------------------------------------------------
@app.route("/api/auth/register", methods=["POST"])
def register():
    # Stage 3 - strict shape check, then per-field validation. A wrong JSON
    # type used to raise AttributeError and return 500; it is now a 400.
    data = v.json_object()
    v.reject_unknown_fields(data, ("name", "email", "password"))

    name = v.clean_text(data.get("name"), "name", max_len=v.MAX_NAME)
    email = v.clean_email(data.get("email"), "email")
    # Type/length only: the password is hashed verbatim and is never trimmed.
    password = v.clean_password(data.get("password"), "password")

    existing = db.query_one("SELECT id FROM users WHERE email = ?", (email,))
    if existing:
        return api_error("An account with this email already exists.", 409)

    token = secrets.token_hex(24)
    now = datetime.utcnow().isoformat(sep=" ")
    user_id = db.execute(
        """INSERT INTO users (name, email, password_hash, api_token,
                              token_expires_at, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (name, email, hash_password(password), token, new_token_expiry(), now),
    )
    user = db.query_one("SELECT * FROM users WHERE id = ?", (user_id,))
    return jsonify({"token": token, "user": user_dict(user)}), 201


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = v.json_object()
    v.reject_unknown_fields(data, ("email", "password"))

    email = v.clean_email(data.get("email"), "email")
    # min_len=0: an over-long or short password must still fall through to the
    # generic 401 below, never to a 400 that would confirm the account exists.
    password = v.clean_password(data.get("password"), "password", min_len=1)

    # Stage 1 token security: the token is still looked up with a bound
    # parameter and is still rejected unless its expiry is valid and future.
    user = db.query_one("SELECT * FROM users WHERE email = ?", (email,))
    if not user or not verify_password(password, user["password_hash"]):
        return api_error("Invalid email or password.", 401)

    # Rotate the token on every successful login so a leaked token has a
    # bounded lifetime and cannot be replayed after the next sign-in.
    token = secrets.token_hex(24)
    db.execute(
        "UPDATE users SET api_token = ?, token_expires_at = ? WHERE id = ?",
        (token, new_token_expiry(), user["id"]),
    )
    return jsonify({"token": token, "user": user_dict(user)})


@app.route("/api/auth/me")
def me():
    user = current_user()
    if not user:
        return api_error("Not authenticated.", 401)
    return jsonify(user_dict(user))


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    # The frontend posts an empty object; anything else in the body is noise.
    v.reject_unknown_fields(v.json_object(required=False), ())
    user = current_user()
    if user:
        db.execute(
            "UPDATE users SET api_token = NULL, token_expires_at = NULL WHERE id = ?",
            (user["id"],),
        )

    return jsonify({"success": True})


# --------------------------------------------------------------------------
# API: checkout / orders
# --------------------------------------------------------------------------
# The documented checkout contract. Anything outside this set is rejected,
# which prevents both typo'd payloads and mass-assignment style surprises.
CHECKOUT_FIELDS = (
    "fullName", "phone", "email", "address", "city", "country",
    "paymentMethod", "items",
)
CHECKOUT_ITEM_FIELDS = ("productId", "quantity")


@app.route("/api/checkout", methods=["POST"])
def checkout():
    data = v.json_object()
    v.reject_unknown_fields(data, CHECKOUT_FIELDS)

    # Stage 3 - the cart was previously trusted for arithmetic. Each field is
    # now bounded: a quantity of 1e9 used to create a $649,990,000,000 order
    # and zero the product's stock.
    full_name = v.clean_text(data.get("fullName"), "fullName", max_len=v.MAX_NAME)
    phone = v.clean_phone(data.get("phone"), "phone")
    email = v.clean_email(data.get("email"), "email")
    address = v.clean_text(
        data.get("address"), "address", max_len=v.MAX_ADDRESS, multiline=True
    )
    city = v.clean_text(data.get("city"), "city", max_len=v.MAX_CITY)
    country = v.clean_text(data.get("country"), "country", max_len=v.MAX_COUNTRY)
    payment = v.clean_choice(
        data.get("paymentMethod"), "paymentMethod", v.PAYMENT_METHODS,
        default="Cash on Delivery",
    )

    items = data.get("items")
    if not isinstance(items, list) or not items:
        raise v.ValidationError("items", "Field 'items' must be a non-empty array.")
    if len(items) > v.MAX_CART_ITEMS:
        raise v.ValidationError(
            "items", "A maximum of %d items is allowed per order." % v.MAX_CART_ITEMS
        )

    subtotal = 0.0
    order_items = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise v.ValidationError(
                "items[%d]" % index, "Field 'items[%d]' must be an object." % index
            )
        v.reject_unknown_fields(item, CHECKOUT_ITEM_FIELDS, context="items[%d]" % index)
        pid = v.clean_int(
            item.get("productId"), "items[%d].productId" % index,
            minimum=1, maximum=v.MAX_ID,
        )
        qty = v.clean_int(
            item.get("quantity"), "items[%d].quantity" % index,
            minimum=1, maximum=v.MAX_QUANTITY_PER_ITEM,
        )
        # productId and quantity are ints now, so neither int() call below can
        # raise, and the lookup stays a bound parameter.
        row = db.query_one("SELECT * FROM products WHERE id = ?", (pid,))
        if not row:
            return api_error("A product in your cart no longer exists.")
        # Stock is the real ceiling: a cart cannot claim more units than exist.
        available = int(row["stock"] or 0)
        if qty > available:
            return api_error("Not enough stock for a product in your cart.")
        price = float(row["price"])
        line_total = round(price * qty, 2)
        subtotal += line_total
        # The English name is stored, so the order keeps rendering in whatever
        # language is requested later rather than being frozen at checkout.
        order_items.append(
            (pid, row["name"], price, qty, line_total, row["image"], available)
        )

    if not order_items:
        return api_error("Your cart is empty.")

    shipping = (
        0.0
        if subtotal >= config.FREE_SHIPPING_THRESHOLD
        else config.SHIPPING_FLAT_RATE
    )
    discount = 0.0
    total = round(subtotal + shipping - discount, 2)

    user = current_user()
    user_id = user["id"] if user else None

    now = datetime.utcnow().isoformat(sep=" ")
    order_id = db.execute(
        """INSERT INTO orders
           (user_id, full_name, phone, email, address, city, country,
            payment_method, subtotal, shipping, discount, total, status, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            user_id, full_name, phone, email, address, city, country, payment,
            round(subtotal, 2), shipping, discount, total, "Pending", now,
        ),
    )

    for (pid, name, price, qty, line_total, image, stock) in order_items:
        db.execute(
            """INSERT INTO order_items (order_id, product_id, name, price, quantity,
                                        subtotal, image) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (order_id, pid, name, price, qty, line_total, image),
        )
        db.execute("UPDATE products SET stock = ? WHERE id = ?", (max(0, stock - qty), pid))

    return jsonify(
        {
            "orderId": order_id,
            "total": total,
            "status": i18n.order_status(lang(), "Pending"),
            # Same pair as the order payloads above: the label is for display,
            # the code is for branching, so a client that keys off `statusCode`
            # does not have to special-case the response to its own checkout.
            "statusCode": "Pending",
        }
    ), 201


@app.route("/api/orders")
def orders():
    user = current_user()
    if not user:
        return api_error("Please log in to view your orders.", 401)
    rows = db.query("SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC", (user["id"],))
    language = lang()
    result = []
    for r in rows:
        detail = order_detail(r, language)
        result.append(detail)
    return jsonify(result)


@app.route("/api/orders/<int:order_id>")
def order(order_id):
    user = current_user()
    # Stage 5 audit fix - broken access control.
    #
    # This used to read:
    #
    #     if user and row["user_id"] != user["id"]:
    #
    # which skipped the ownership test entirely whenever the caller was not
    # logged in, so `GET /api/orders/<id>` returned any order in the shop -
    # full name, phone, email and street address - to a completely anonymous
    # client. Order ids are sequential integers, so the whole order table was
    # enumerable by counting.
    #
    # Authentication is now required first, and an order is only returned when
    # the caller owns it. "Missing" and "not yours" deliberately share one 404
    # so a caller cannot use the status code to discover which order ids exist.
    if not user:
        return api_error("Please log in to view your orders.", 401)
    row = db.query_one("SELECT * FROM orders WHERE id = ?", (order_id,))
    if not row or row["user_id"] != user["id"]:
        return api_error("Order not found.", 404)
    return jsonify(order_detail(row, lang()))


def order_detail(row, language=i18n.DEFAULT_LANGUAGE):
    items = db.query(
        """SELECT product_id, name, price, quantity, subtotal, image
           FROM order_items WHERE order_id = ?""",
        (row["id"],),
    )
    # Stage 3 - the order history renders `it.image` in an <img src>, so the
    # stored path is re-validated on the way out rather than trusted because it
    # was validated on the way in.
    for item in items:
        item["image"] = v.safe_media_path(
            item.get("image"), "image", fallback="/uploads/accessories.svg"
        )
        # Line items are stored with the English product name so that an order
        # placed in one language still reads correctly in another; a name with
        # no product row behind it (a deleted product) passes through as-is.
        localized, _ = i18n.product_text(language, item.get("name") or "", "")
        item["name"] = localized
    return {
        "id": int(row["id"]),
        "fullName": row["full_name"],
        "phone": row["phone"],
        "email": row["email"],
        "address": row["address"],
        "city": row["city"],
        "country": row["country"],
        # `paymentMethodCode` and `statusCode` carry the stored enum values so a
        # client can still branch on them without string-matching a translation.
        "paymentMethod": i18n.payment_method(language, row["payment_method"]),
        "paymentMethodCode": row["payment_method"],
        "subtotal": round(float(row["subtotal"]), 2),
        "shipping": round(float(row["shipping"]), 2),
        "discount": round(float(row["discount"]), 2),
        "total": round(float(row["total"]), 2),
        "status": i18n.order_status(language, row["status"]),
        "statusCode": row["status"],
        "createdAt": row["created_at"],
        "items": items,
    }


# --------------------------------------------------------------------------
# Static files (uploads + built frontend)
# --------------------------------------------------------------------------
@app.route("/uploads/<path:filename>")
def uploads(filename):
    # Stage 3 - reject traversal attempts, separators and control characters
    # with a 400 before the filesystem is touched. send_from_directory already
    # blocks traversal, so this is a second, explicit layer.
    safe_name = v.clean_filename(filename, "filename")
    return send_from_directory(config.UPLOAD_DIR, safe_name)


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def spa(path):
    # Stage 5 audit fix - the original test was `path.startswith("api/")`, which
    # does not match the bare path "api", so `GET /api` fell through to the
    # SPA branch and answered 200 text/html with the whole app shell. An API
    # client that probes the API root now gets the same JSON 404 as every other
    # unknown /api path instead of being handed a page of HTML.
    if path == "api" or path.startswith("api/"):
        return api_error("Not found", 404)
    if path == "uploads" or path.startswith("uploads/"):
        return api_error("Not found", 404)
    index = os.path.join(config.FRONTEND_DIST, "index.html")
    # Stage 3 - only a plain, relative asset path may be served. Rejecting
    # absolute paths, dot-segments and control characters here means a crafted
    # URL can never escape the frontend/dist directory.
    if path:
        if (
            ".." in path
            or path.startswith(("/", "\\"))
            or "\x00" in path
            or "\\" in path
        ):
            return api_error("Not found", 404)
        asset = os.path.join(config.FRONTEND_DIST, path)
        if os.path.isfile(asset):
            return send_from_directory(config.FRONTEND_DIST, path)
    if os.path.isfile(index):
        return send_from_directory(config.FRONTEND_DIST, "index.html")
    # This branch is a developer hint, not a user-facing page, but it is still
    # localised so a non-English developer is not told what to do in English.
    return Response(
        i18n.error_message(
            lang(),
            "Frontend not built yet. Run `npm install && npm run build` inside the frontend folder.",
        ),
        status=200,
    )


# --------------------------------------------------------------------------
# Stage 4 - attach the per-endpoint rate limits
# --------------------------------------------------------------------------
# This wraps the already-registered view functions with the limiter. It runs
# last (after every route exists) and changes no handler logic - each view is
# only wrapped, so request handling, token checks, CORS and validation are all
# exactly as they were in Stages 1-3.
_applied = rate_limit.apply_all(app, limiter)
print("[stage4] rate limiting %s (%s)" % (
    "enabled" if config.RATE_LIMIT_ENABLED else "DISABLED",
    ", ".join(_applied) if _applied else "default limits only",
))
if config.TRUST_PROXY:
    print("[stage4] WARNING: TRUST_PROXY is on - ensure a reverse proxy "
          "overwrites X-Forwarded-For, or clients can spoof their IP.")


# --------------------------------------------------------------------------
# Stage 2 - CORS startup validation
# --------------------------------------------------------------------------
# Fail fast if the live app does not behave exactly like the policy: an allowed
# origin must be echoed back, and an untrusted origin must receive no CORS
# headers at all. This runs at import time (so `python app.py` and `import app`
# both validate) and must stay below every route definition, because issuing a
# test request finalises Flask's setup.
cors_config.verify_cors_policy(app, config.CORS_POLICY)
print(cors_config.describe(config.CORS_POLICY))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("Naly,munib backend listening on http://localhost:%d (DB: %s)" % (port, db.backend_name))
    app.run(host="0.0.0.0", port=port, debug=False)