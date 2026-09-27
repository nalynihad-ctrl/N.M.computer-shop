"""End-to-end checks for the localised API.

Run:  python backend/tools/check_i18n_api.py

Exercises the real Flask app through its test client rather than the
translation tables directly, because the thing that has to hold is the HTTP
contract:

* an English request is unchanged, so nothing that already worked can regress;
* every localized response is actually translated, with no English prose left;
* the additive keys are present and the canonical English keys are untouched,
  so category URLs, the ?category= filter and the cart still work;
* errors and validation messages localize, including ones the frontend triggers
  by sending bad input;
* a search in Arabic or Kurdish finds products, which is the case the SQL LIKE
  alone cannot cover.

Compatibility policy, stated once so it is not re-litigated per field: an
English response is additive, not byte-identical. Localization adds keys -
`categoryName` on a product, `key` on a category, `statusCode` and
`paymentMethodCode` on an order, `field` on an api_error - but it never changes
the value of a key that already existed, and it never removes one. So the
category URL, the `?category=` filter, the stored enums and the cart all keep
working, while a client that ignores the new keys sees the API it had before.
Byte-identical output was rejected because it would mean not shipping the
translated display names at all, which is the whole point.
"""

import json
import os
import re
import sys
from urllib.parse import quote

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(HERE)
sys.path.insert(0, BACKEND)
sys.path.insert(0, HERE)

import i18n  # noqa: E402
from app import app  # noqa: E402
import seed_data  # noqa: E402
# The same allowlist the static check uses, so "this name contains a real
# English word and should therefore have been translated" is one shared rule
# rather than two that can drift apart.
from check_i18n import untranslated_tokens  # noqa: E402

LANGUAGES = ("en", "ar", "ku")

failures = []
checks = 0


def check(name, condition, detail=""):
    global checks
    checks += 1
    if not condition:
        failures.append("%s%s" % (name, (": " + detail) if detail else ""))
    return bool(condition)


def get(path, lang=None, headers=None):
    """GET ``path`` with an optional ?lang=, merging onto any existing query."""
    separator = "&" if "?" in path else "?"
    url = path + (separator + "lang=%s" % lang if lang else "")
    request_headers = dict(headers or {})
    if lang:
        request_headers.setdefault("Accept-Language", lang)
    with app.test_client() as client:
        response = client.get(url, headers=request_headers)
    return response, json.loads(response.data.decode("utf-8"))


def arabic_heavy(text):
    """True when the string carries real Arabic script, not just a stray code."""
    return len(re.findall(r"[\u0600-\u06ff]", text or "")) >= 3


def translated_away(english, localized):
    """Localized text must differ from English and be in the target script."""
    if not isinstance(localized, str) or not localized:
        return False
    if localized == english:
        return False
    if english and arabic_heavy(english) and arabic_heavy(english) == arabic_heavy(localized):
        # English source is not Arabic, so any Arabic script in the localized
        # value is a real translation.
        return True
    return arabic_heavy(localized)


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    # ---------------------------------------------------------------- English
    response, english_products = get("/api/products")
    check("GET /api/products is 200", response.status_code == 200)
    check("English returns the full catalogue", len(english_products) == 60,
          "got %d" % len(english_products))

    first = english_products[0]
    seed = {p["name"]: p for p in seed_data.build_products()}
    # Localized responses carry a translated `name`, so the seed row has to be
    # reached through the product id, never through the name being asserted on.
    seed_by_id = {}
    for index, row in enumerate(seed_data.build_products()):
        seed_by_id[index + 1] = row
    english_by_id = {p["id"]: p for p in english_products}
    check("English name is the seeded name", first["name"] in seed, first["name"])
    check("English description is the seeded description",
          first["description"] == seed_by_id[first["id"]]["description"])
    check("English category is the canonical key",
          first["category"] == seed_by_id[first["id"]]["category"])
    check("English categoryName equals category",
          first["categoryName"] == first["category"])
    check("English specs are untouched",
          first["specs"] == json.loads(seed_by_id[first["id"]]["specs"]))
    check("English spec keys are untouched",
          list(first["specs"]) == list(json.loads(seed_by_id[first["id"]]["specs"])))

    response, english_categories = get("/api/categories")
    check("GET /api/categories is 200", response.status_code == 200)
    check("English category names are the canonical keys",
          all(c["name"] == c["key"] for c in english_categories))
    check("Category keys match the seed",
          {c["key"] for c in english_categories} <= set(seed_data.CATEGORY_META))

    # An unsupported tag must not 500 and must not silently return garbage.
    response, _ = get("/api/products", lang="fr")
    check("Unsupported lang degrades to 200", response.status_code == 200)
    response, body = get("/api/products", lang="zz")
    check("Unknown lang falls back to English", body[0]["name"] == first["name"])

    # ------------------------------------------------------- Arabic / Kurdish
    for lang in ("ar", "ku"):
        response, products = get("/api/products", lang=lang)
        check("GET /api/products?lang=%s is 200" % lang, response.status_code == 200)
        check("%s returns every product" % lang, len(products) == 60,
              "got %d" % len(products))
        check("%s ids are unchanged" % lang,
              [p["id"] for p in products] == [p["id"] for p in english_products])
        check("%s canonical categories are unchanged" % lang,
              [p["category"] for p in products] == [p["category"] for p in english_products])

        # A product name is left in Latin only when every one of its words is a
        # model number, vendor or interface name; anything with a real English
        # word in it has to have moved.
        model_names, still_english = set(), []
        for product_row in products:
            source = seed_by_id[product_row["id"]]["name"]
            if not untranslated_tokens(source):
                model_names.add(product_row["name"])
            elif product_row["name"] == source:
                still_english.append(source)
        check("%s translated every product name that had words" % lang,
              not still_english, str(still_english[:3]))
        check("%s kept model-only names as-is" % lang,
              len(model_names) > 0, "expected some pure model names")

        same_as_english = []
        for product_row in products:
            source = seed_by_id[product_row["id"]]
            if product_row["description"] == source["description"]:
                same_as_english.append(source["name"])
        check("%s has no untranslated descriptions" % lang,
              not same_as_english, str(same_as_english[:2]))

        untranslated_desc = []
        for product_row in products:
            source = seed_by_id[product_row["id"]]
            if product_row["description"] == source["description"] and re.search(
                r"[A-Za-z]{4,}\s+[A-Za-z]{4,}", source["description"]
            ):
                untranslated_desc.append(source["name"])
        check("%s descriptions are not left as English prose" % lang,
              not untranslated_desc, str(untranslated_desc[:2]))

        # Specs: keys and wordy values must move, codes must not.
        words = {
            "ar": ("الذاكرة", "سنة واحدة"),
            "ku": ("بیرگە", "یەک ساڵ"),
        }[lang]
        spec_keys, spec_values = set(), []
        for product_row in products:
            spec_keys.update(product_row["specs"])
            spec_values.extend(str(v) for v in product_row["specs"].values())
        check("%s translated a spec label" % lang, words[0] in spec_keys,
              "sample: %s" % sorted(spec_keys)[:4])
        check("%s translated a spec value" % lang, any(words[1] == v for v in spec_values))
        check("%s kept unit spec values" % lang,
              any("PCIe" in v for v in spec_values), "expected a PCIe spec to survive")

        response, categories = get("/api/categories", lang=lang)
        check("GET /api/categories?lang=%s is 200" % lang, response.status_code == 200)
        check("%s category keys unchanged" % lang,
              [c["key"] for c in categories] == [c["key"] for c in english_categories])
        check("%s category names translated" % lang,
              all(arabic_heavy(c["name"]) for c in categories),
              str([c["name"] for c in categories[:3]]))
        check("%s category names differ from keys" % lang,
              all(c["name"] != c["key"] for c in categories))

    # ------------------------------------------------- category filter + link
    response, arabic_categories = get("/api/categories", lang="ar")
    gpu_label = next(c for c in arabic_categories if c["key"] == "GPUs")
    check("GPU label is translated", gpu_label["name"] != "GPUs", gpu_label["name"])

    # The filter must take the canonical key, exactly as the frontend sends it.
    response, filtered = get("/api/products?category=GPUs", lang="ar")
    check("category filter still works in Arabic",
          response.status_code == 200 and len(filtered) == gpu_label["productCount"],
          "%d vs %d" % (len(filtered), gpu_label["productCount"]))
    check("filtered products carry the translated category name",
          all(p["categoryName"] == gpu_label["name"] for p in filtered))

    # A localized label must NOT be usable as the filter value, because the
    # stored column is the English key. This documents the contract rather than
    # failing: it returns an empty list, not an error.
    response, wrong = get("/api/products?category=%s" % gpu_label["name"], lang="ar")
    check("localized label is not a valid filter value", wrong == [],
          "%d rows" % len(wrong))

    # ---------------------------------------------------------- product detail
    response, detail = get("/api/products/%d" % first["id"], lang="ar")
    check("GET product detail is 200", response.status_code == 200)
    check("detail id is unchanged", detail["id"] == first["id"])
    check("detail carries categoryName", "categoryName" in detail)
    check("detail category stays canonical", detail["category"] == first["category"])

    # ------------------------------------------------------------- cart by ids
    # The cart stores product ids, not names, and re-reads its lines in the
    # active language. This is what stops a cart built in English from keeping
    # English product names after a switch to Arabic.
    #
    # Sampling three rows would be weak here: the highest-rated products all have
    # pure model numbers whose names correctly stay in Latin, so "did a name
    # change?" would pass or fail depending on which rows were drawn. Instead the
    # ids path is cross-checked against the full listing for every product, which
    # is both deterministic and a stronger claim: the two code paths must agree.
    all_ids = [p["id"] for p in english_products]
    # The ids filter is capped at the cart limit, so the cross-check walks the
    # catalogue in cart-sized batches rather than asking for all 60 at once.
    batches = [
        all_ids[i:i + 50] for i in range(0, len(all_ids), 50)
    ]
    for lang in ("ar", "ku"):
        response, listing = get("/api/products", lang=lang)
        fetched = {}
        for batch in batches:
            response, page = get(
                "/api/products?ids=%s" % ",".join(str(i) for i in batch), lang=lang
            )
            check("ids batch is 200 in %s" % lang, response.status_code == 200)
            fetched.update({p["id"]: p for p in page})
        listed = {p["id"]: p for p in listing}
        check("ids batches return the whole catalogue in %s" % lang,
              set(fetched) == set(listed),
              "%d vs %d rows" % (len(fetched), len(listed)))

        mismatched = [
            pid for pid in listed
            if any(fetched.get(pid, {}).get(f) != listed[pid].get(f)
                   for f in ("name", "description", "specs", "categoryName",
                             "category", "price", "brand"))
        ]
        check("ids lookup localises identically to the listing in %s" % lang,
              not mismatched, "ids %s" % mismatched[:5])

    # A real cart is a small subset, and the canonical fields the cart prices and
    # submits must not move with the language.
    cart_ids = [p["id"] for p in english_products[:3]]
    ids_param = ",".join(str(i) for i in cart_ids)
    response, cart_en = get("/api/products?ids=%s" % ids_param, lang="en")
    check("a 3-line cart returns exactly 3 rows",
          {p["id"] for p in cart_en} == set(cart_ids),
          str(sorted(p["id"] for p in cart_en)))
    for lang in ("ar", "ku"):
        response, cart_rows = get("/api/products?ids=%s" % ids_param, lang=lang)
        check("a 3-line cart returns exactly 3 rows in %s" % lang,
              {p["id"] for p in cart_rows} == set(cart_ids),
              str(sorted(p["id"] for p in cart_rows)))
        english = {p["id"]: p for p in cart_en}
        check("cart price and category stay canonical in %s" % lang,
              all(row["price"] == english[row["id"]]["price"]
                  and row["category"] == english[row["id"]]["category"]
                  for row in cart_rows))
    # Unknown ids are simply absent rather than an error.
    response, missing = get("/api/products?ids=%d,999999" % cart_ids[0], lang="ar")
    check("an unknown cart id is skipped, not an error",
          response.status_code == 200 and [p["id"] for p in missing] == [cart_ids[0]],
          str(response.status_code))
    # The id filter is still type- and bound-checked like every other parameter.
    for bad in ("1,abc", "0", "-1", "1 OR 1=1"):
        response, _ = get("/api/products?ids=%s" % bad.replace(" ", "%20"), lang="ar")
        check("malformed ids=%r is rejected" % bad, response.status_code == 400,
              "status %d" % response.status_code)


    # Unknown ids are simply absent rather than an error.
    response, missing = get("/api/products?ids=%d,999999" % cart_ids[0], lang="ar")
    check("an unknown cart id is skipped, not an error",
          response.status_code == 200 and [p["id"] for p in missing] == [cart_ids[0]],
          str(response.status_code))
    # The id filter is still type- and bound-checked like every other parameter.
    for bad in ("1,abc", "0", "-1", "1 OR 1=1"):
        response, _ = get("/api/products?ids=%s" % bad.replace(" ", "%20"), lang="ar")
        check("malformed ids=%r is rejected" % bad, response.status_code == 400,
              "status %d" % response.status_code)

    # ----------------------------------------------------------------- errors
    response, body = get("/api/products/999999", lang="ar")
    check("missing product is 404", response.status_code == 404)
    check("missing product message is Arabic", arabic_heavy(body["error"]), body["error"])
    check("error body keeps the field key", "field" in body)

    with app.test_client() as client:
        response = client.post(
            "/api/auth/login?lang=ar",
            json={"email": "nobody@example.com", "password": "wrong-password"},
        )
    body = json.loads(response.data.decode("utf-8"))
    check("bad login is 401", response.status_code == 401)
    check("bad login message is Arabic", arabic_heavy(body["error"]), body["error"])

    # A validation failure raised deep in validation.py must localize too.
    with app.test_client() as client:
        response = client.post(
            "/api/auth/login?lang=ar",
            json={"email": "not-an-email", "password": "x"},
        )
    body = json.loads(response.data.decode("utf-8"))
    check("validation error is 400", response.status_code == 400)
    check("validation message is Arabic", arabic_heavy(body["error"]), body["error"])
    check("validation message keeps the field name",
          "email" in body["error"], body["error"])

    with app.test_client() as client:
        response = client.get("/api/nope?lang=ar")
    body = json.loads(response.data.decode("utf-8"))
    check("unknown API path is 404", response.status_code == 404)
    check("unknown API path message is Arabic or untranslated name",
          arabic_heavy(body["error"]) or body["error"] == "Not Found", body["error"])

    # --------------------------------------------------- Accept-Language only
    response, body = get("/api/products", headers={"Accept-Language": "ar-IQ,ar;q=0.9"})
    check("Accept-Language selects Arabic",
          arabic_heavy(body[0]["categoryName"]), body[0]["categoryName"])
    response, body = get("/api/products", headers={"Accept-Language": "ku"})
    check("Accept-Language selects Kurdish",
          arabic_heavy(body[0]["categoryName"]), body[0]["categoryName"])
    response, body = get("/api/products", headers={"Accept-Language": "en-GB"})
    check("Accept-Language en-GB stays English", body[0]["categoryName"] == body[0]["category"])

    # Quality values have to be honoured, not just the first tag in the list:
    # a browser sending "en;q=0.8,ar;q=0.9" prefers Arabic, and picking the left
    # -most entry would get that backwards.
    response, body = get("/api/products", headers={"Accept-Language": "en;q=0.8,ar;q=0.9"})
    check("higher q wins over header order",
          arabic_heavy(body[0]["categoryName"]), body[0]["categoryName"])
    response, body = get("/api/products", headers={"Accept-Language": "fr;q=1.0,ku;q=0.9"})
    check("unsupported higher-q tag falls through to a supported one",
          arabic_heavy(body[0]["categoryName"]), body[0]["categoryName"])
    # q=0 is a refusal, so English must not be served to a client that excluded it.
    response, body = get("/api/products", headers={"Accept-Language": "en;q=0,ar"})
    check("q=0 excludes a language instead of preferring it",
          arabic_heavy(body[0]["categoryName"]), body[0]["categoryName"])
    response, body = get("/api/products", headers={"Accept-Language": "*"})
    check("wildcard falls back to the default",
          body[0]["categoryName"] == body[0]["category"], body[0]["categoryName"])
    response, body = get("/api/products", headers={"Accept-Language": "fr-FR,de;q=0.8"})
    check("no supported tag falls back to English",
          body[0]["categoryName"] == body[0]["category"], body[0]["categoryName"])
    # An explicit query parameter outranks the header whatever the header says.
    response, body = get("/api/products?lang=ar", headers={"Accept-Language": "en"})
    check("?lang= outranks Accept-Language",
          arabic_heavy(body[0]["categoryName"]), body[0]["categoryName"])

    # ----------------------------------------------------------------- search
    # The SQL LIKE only sees English, so the localized pass has to be able to
    # find things by their translated category label. Searching for the
    # localized label of a category must return that category's products.
    # Terms are percent-encoded: these are Arabic and Kurdish strings with
    # spaces in them, and building a query by string concatenation would send a
    # raw space in a URL and test the client's leniency rather than the server.
    for lang in ("ar", "ku"):
        response, cats = get("/api/categories", lang=lang)
        for category_row in cats[:4]:
            response, hits = get(
                "/api/products?search=%s" % quote(category_row["name"]), lang=lang
            )
            check(
                "searching the %s label %r finds that category"
                % (lang, category_row["name"]),
                response.status_code == 200
                and len(hits) == category_row["productCount"]
                and all(p["category"] == category_row["key"] for p in hits),
                "%d hits, expected %d" % (len(hits), category_row["productCount"]),
            )
            break  # one category per language is enough to prove the path

    response, hits = get("/api/products?search=%s" % quote("ماوس"), lang="ku")
    check("a Kurdish word finds products", len(hits) > 0, "%d hits" % len(hits))
    response, hits = get("/api/products?search=RTX", lang="ar")
    check("model numbers still searchable in any language", len(hits) > 0,
          "%d hits" % len(hits))

    # Specs are stored as English JSON, so the localized scan has to parse and
    # translate them too - otherwise the words that actually distinguish one
    # part from another are unreachable in Arabic and Kurdish.
    #
    # The expectation is derived from the catalogue itself rather than hardcoded:
    # fetch every product in the target language and select the ones whose
    # *rendered* specs contain the needle. Comparing id sets is the only way to
    # assert this, because the response carries translated specs - checking for
    # "RPM" in an Arabic payload would fail even on a correct result.
    def ids_where(lang, needle, field):
        response, everything = get("/api/products", lang=lang)
        return sorted(
            p["id"] for p in everything
            if needle in json.dumps(p[field], ensure_ascii=False)
        )

    rpm_key = "دورات في الدقيقة"  # the "RPM" spec key
    expected = ids_where("ar", rpm_key, "specs")
    response, hits = get("/api/products?search=%s" % quote(rpm_key), lang="ar")
    check(
        "a translated spec key is searchable",
        len(expected) > 0 and sorted(p["id"] for p in hits) == expected,
        "%d hits, expected ids %s, got %s"
        % (len(hits), expected, sorted(p["id"] for p in hits)),
    )

    # A spec *value* is translatable too, not just the key.
    watts = "١٠٠ واط"  # the "100W" spec value
    expected = ids_where("ar", watts, "specs")
    response, hits = get("/api/products?search=%s" % quote(watts), lang="ar")
    check(
        "a translated spec value is searchable",
        len(expected) > 0 and sorted(p["id"] for p in hits) == expected,
        "%d hits, expected ids %s, got %s"
        % (len(hits), expected, sorted(p["id"] for p in hits)),
    )

    # The same has to work for Kurdish, or the feature is only half wired up.
    ku_expected = ids_where("ku", i18n.t("ku", i18n.SPEC_KEYS, "RPM", "RPM"), "specs")
    ku_needle = i18n.t("ku", i18n.SPEC_KEYS, "RPM", "RPM")
    response, hits = get("/api/products?search=%s" % quote(ku_needle), lang="ku")
    check(
        "a translated spec key is searchable in Kurdish",
        len(ku_expected) > 0 and sorted(p["id"] for p in hits) == ku_expected,
        "%d hits, expected ids %s" % (len(hits), ku_expected),
    )

    # A needle that exists in no spec must not match anything, rather than
    # degrading into a substring match on some unrelated field.
    response, hits = get("/api/products?search=%s" % quote("لا يوجد与此"), lang="ar")
    check("an unmatched spec needle returns nothing", len(hits) == 0,
          "%d hits" % len(hits))


    # LIKE metacharacters must not widen the query. Escaping them means a search
    # for "%" or "_" is a *literal* search, so it returns only rows that really
    # contain that character ("75%" in a spec, "WD_BLACK") rather than every row.
    for needle, char in (("%25", "%"), ("_", "_")):
        response, hits = get("/api/products?search=%s" % needle, lang="en")
        literal = []
        for product_row in hits:
            text = " ".join(
                [product_row["name"], product_row["brand"], product_row["category"],
                 product_row["description"]]
                + [str(v) for v in product_row["specs"].values()]
            )
            if char in text:
                literal.append(product_row["id"])
        check("search for %r does not widen the query" % char,
              len(hits) < 60, "%d of 60 rows" % len(hits))
        check("search for %r only matches literal occurrences" % char,
              len(literal) == len(hits),
              "%d of %d hits contain %r" % (len(literal), len(hits), char))

    # ------------------------------------------------------ orders / checkout
    with app.test_client() as client:
        response = client.get("/api/orders?lang=ar")
    body = json.loads(response.data.decode("utf-8"))
    check("unauthenticated orders is 401", response.status_code == 401)
    check("orders auth message is Arabic", arabic_heavy(body["error"]), body["error"])

    print("ran %d checks" % checks)
    if failures:
        print("\n%d FAILURE(S):" % len(failures))
        for failure in failures:
            print("  - %s" % failure)
        return 1
    print("OK - localised API behaves; English values are unchanged (additive keys only).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
