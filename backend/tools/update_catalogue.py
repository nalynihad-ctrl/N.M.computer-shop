"""One-off migration: swap placeholder SVGs for high-res product photos and
add the Microphones category (products). Idempotent - safe to re-run.
"""

import json
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config  # noqa: E402
from db import Database  # noqa: E402
from seed_data import build_products  # noqa: E402


def main():
    db = Database(config.MYSQL_CONFIG, config.MYSQL_DATABASE, config.SQLITE_PATH)
    db.init_schema()

    now = datetime.utcnow()
    updated = 0
    inserted = 0

    for p in build_products():
        images = json.dumps([p["image"]])
        existing = db.query_one("SELECT id FROM products WHERE name = ?", (p["name"],))
        if existing:
            db.execute(
                "UPDATE products SET image = ?, images = ? WHERE id = ?",
                (p["image"], images, existing["id"]),
            )
            updated += 1
        else:
            db.execute(
                """INSERT INTO products
                   (name, brand, category, description, price, old_price, discount,
                    image, images, stock, rating, specs, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    p["name"], p["brand"], p["category"], p["description"],
                    p["price"], p["old_price"], p["discount"], p["image"],
                    images, p["stock"], p["rating"], p["specs"],
                    (now - timedelta(days=p["days_ago"])).isoformat(sep=" "),
                ),
            )
            inserted += 1

    print("[update_catalogue] updated=%d inserted=%d (DB: %s)" % (updated, inserted, db.backend_name))


if __name__ == "__main__":
    main()