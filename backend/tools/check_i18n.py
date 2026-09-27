"""Static checks for backend/i18n.py.

Run:  python backend/tools/check_i18n.py

Guards the translation tables against the failure modes that a hand-written
catalogue actually hits:

1. duplicate dict keys, which Python silently collapses so the first or the
   last definition wins depending on how the file is parsed;
2. product keys that do not match the seed catalogue, or seed products with no
   translation;
3. values that picked up characters from an unrelated script;
4. English words left sitting inside an Arabic or Kurdish sentence, which is the
   common sign of a botched copy/paste;
5. spec keys/values in use that have no translation at all.
"""

import ast
import json
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(HERE)
sys.path.insert(0, BACKEND)

import i18n  # noqa: E402
import seed_data  # noqa: E402

I18N_PATH = os.path.join(BACKEND, "i18n.py")

TABLES = {
    "CATEGORY_NAMES": i18n.CATEGORY_NAMES,
    "ORDER_STATUSES": i18n.ORDER_STATUSES,
    "PAYMENT_METHODS": i18n.PAYMENT_METHODS,
    "ERRORS": i18n.ERRORS,
    "VALIDATION_MESSAGES": i18n.VALIDATION_MESSAGES,
    "SPEC_KEYS": i18n.SPEC_KEYS,
    "SPEC_VALUES": i18n.SPEC_VALUES,
    "PRODUCTS": i18n.PRODUCTS,
}

# Scripts that must never appear in a translation value.
FOREIGN_SCRIPTS = {
    "CJK": r"\u3000-\u303f\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff",
    "Cyrillic": r"\u0400-\u04ff",
    "Greek": r"\u0370-\u03ff",
    "Hebrew": r"\u0590-\u05ff",
    "Devanagari": r"\u0900-\u097f",
    "Thai": r"\u0e00-\u0e7f",
}

FOREIGN = {name: re.compile(pattern) for name, pattern in FOREIGN_SCRIPTS.items()}

# Characters that legitimately appear in technical strings we keep verbatim.
ALLOWED_EXTRA = set("×÷°®™±≥≤•…–—→←↔'%\"\u200b\u200c\u200d\u200e\u200f")

# The two scripts the translations are written in, plus Arabic-Indic digits.
EXPECTED_RANGES = (
    (0x0600, 0x06FF),  # Arabic
    (0x0750, 0x077F),  # Arabic Supplement
    (0xFB50, 0xFDFF),  # Arabic Presentation Forms-A
    (0xFE70, 0xFEFF),  # Arabic Presentation Forms-B
)


def in_expected_script(char):
    code = ord(char)
    if code < 0x80:
        return True
    if char in ALLOWED_EXTRA:
        return True
    return any(lo <= code <= hi for lo, hi in EXPECTED_RANGES)

# Latin tokens that are expected to survive translation verbatim: vendor
# names, model families, bus/interface names and units. This is deliberately a
# short, reviewable list - a new English word showing up here is the signal
# that it should be translated instead of allow-listed.
TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9]*(?:[-/.+'][A-Za-z0-9]+)*")

TECHNICAL_TOKENS = {
    # vendors and model families
    "RTX", "GTX", "RX", "Arc", "GeForce", "Radeon", "Ryzen", "Threadripper",
    "Core", "i5", "i7", "i9", "Xeon", "W", "HX", "HS",
    # buses, slots and interfaces
    "PCIe", "USB", "USB-C", "USB-A", "USB/XLR", "XLR", "HDMI", "VGA", "DVI",
    "DisplayPort", "SATA", "NVMe", "M.2", "LAN", "ATX", "ITX", "E-ATX",
    "Micro-ATX", "MicroATX", "MT/s", "MB/s", "GB/s", "TN",
    # memory and clocks
    "DDR", "DDR4", "DDR5", "GDDR6", "GDDR7", "CL", "MT", "MHz", "GHz",
    # sockets and standards
    "AM", "AM4", "AM5", "LGA", "WiFi", "Bluetooth", "QMK", "VIA", "EXPO", "XMP",
    # displays
    "QHD", "FHD", "UHD", "WQHD", "QWHD", "IPS", "VA", "OLED", "HDR", "Hz",
    "WQXGA",
    # lighting
    "RGB", "ARGB", "LED", "LCD", "Chroma", "PLUS",
    # units
    "GB", "TB", "MB", "KB", "Mbps", "Gbps", "mAh", "mm", "cm", "inch", "nm",
    "dB", "Wh", "III", "II", "Gen",
    # named technologies that are trademarks, not descriptive words
    "HERO", "Focus", "ClearCast", "HyperClear", "Cardioid", "BAMF",
    "Gateron", "Tactile", "Razer", "G-Skill", "HyperX", "SteelSeries",
    "Arctic", "Logitech", "Acer", "Lenovo", "ASUS", "MSI", "Gigabyte",
    "ASRock", "Corsair", "NZXT", "Seasonic", "EVGA", "Noctua", "Lian",
    "Samsung", "Seagate", "Crucial", "Western", "Digital", "WD", "TP-Link",
    "NETGEAR", "Shure", "Blue", "Yeti", "Audio-Technica", "Keychron",
    "Glorious", "Kingston", "Thermalright", "BlackWidow", "DeathAdder",
    "Seiren", "QuadCast", "Cloud", "Arctis", "Zephyrus", "Legion", "Nitro",
    "Model", "Trident", "Fury", "Beast", "Vengeance", "BarraCuda", "IronWolf",
    "Pro", "Plus", "Force", "Focus", "Trident",
    # shell command words, which are quoted verbatim in a build hint
    "npm", "install", "run", "build", "cd",
    # measurement words that read as units
    "g", "k", "C", "T", "S",
}

# A token is an identifier, not a word, if it is a single character (always a
# fragment like the "x" in "x16" or the "p" in "1080p") or if it mixes letters
# and digits (like "GDDR7", "i5-13420H", "x1080"). Neither can be a stray
# English word, so both are accepted without listing every compound by hand.
IDENTIFIER = re.compile(r"^" + TOKEN.pattern.replace("[A-Za-z]", "[A-Za-z0-9]") + r"$")


def untranslated_tokens(value):
    """Latin tokens in ``value`` that are not technical identifiers."""
    out = set()
    for token in TOKEN.findall(value):
        if token in TECHNICAL_TOKENS:
            continue
        if len(token) == 1 or IDENTIFIER.match(token):
            continue
        out.add(token)
    return sorted(out)



def fail(problems, message):
    problems.append(message)


def check_duplicate_keys(problems):
    """Detect duplicate keys in the literal tables, which Python hides."""
    with open(I18N_PATH, encoding="utf-8") as handle:
        tree = ast.parse(handle.read(), filename=I18N_PATH)

    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
        name = targets[0] if targets else None
        if name not in TABLES or not isinstance(node.value, ast.Dict):
            continue
        seen = {}
        for key in node.value.keys:
            if key is None:
                continue
            try:
                literal = ast.literal_eval(key)
            except (ValueError, SyntaxError):
                continue
            seen[literal] = seen.get(literal, 0) + 1
        for literal, count in seen.items():
            if count > 1:
                fail(
                    problems,
                    "%s: key %r defined %d times (line %d)"
                    % (name, literal, count, getattr(key, "lineno", "?")),
                )


def seed_products():
    return seed_data.build_products()


def check_products(problems):
    seeded = {p["name"]: p for p in seed_products()}
    table = i18n.PRODUCTS

    for name in sorted(set(seeded) - set(table)):
        fail(problems, "PRODUCTS: no translation for seeded product %r" % name)
    for name in sorted(set(table) - set(seeded)):
        fail(problems, "PRODUCTS: %r is not in seed_data" % name)

    # The translated name must not itself be a different product's name.
    names = {p["name"] for p in seed_products()}
    for key, entry in table.items():
        for lang in ("ar", "ku"):
            value = (entry.get(lang) or {}).get("name")
            if value in names and value != key:
                fail(
                    problems,
                    "PRODUCTS[%r][%r].name is %r, which is another product's name"
                    % (key, lang, value),
                )


def check_categories(problems):
    seeded = {c["name"] if isinstance(c, dict) else c for c in seed_data.CATEGORY_META}
    if isinstance(seed_data.CATEGORY_META, dict):
        seeded = set(seed_data.CATEGORY_META)
    for name in sorted(set(seeded) - set(i18n.CATEGORY_NAMES)):
        fail(problems, "CATEGORY_NAMES: no translation for %r" % name)
    for name in sorted(set(i18n.CATEGORY_NAMES) - set(seeded)):
        fail(problems, "CATEGORY_NAMES: %r is not a real category" % name)


def walk_strings(value, path=""):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from walk_strings(item, "%s.%s" % (path, key) if path else str(key))
    elif isinstance(value, str):
        yield path, value


def check_scripts(problems):
    for table_name, table in TABLES.items():
        for path, value in walk_strings(table, table_name):
            for script, pattern in FOREIGN.items():
                match = pattern.search(value)
                if match:
                    fail(
                        problems,
                        "%s: %s contains %s character %r"
                        % (path, script, script, match.group()),
                    )
            bad = {c for c in value if not in_expected_script(c)}
            if bad:
                fail(
                    problems,
                    "%s: stray characters %s"
                    % (path, ", ".join("%r (U+%04X %s)" % (c, ord(c), unicodedata.name(c, "?"))
                                       for c in sorted(bad))),
                )


def check_embedded_latin(problems):
    """Flag English words left inside an Arabic/Kurdish value."""
    for table_name, table in TABLES.items():
        for path, value in walk_strings(table, table_name):
            if not (path.endswith(".ar") or path.endswith(".ku")):
                continue
            for token in untranslated_tokens(value):
                fail(problems, "%s: untranslated Latin token %r" % (path, token))


def check_spec_coverage(problems, verbose):
    used_keys, used_values = set(), set()
    for product in seed_products():
        specs = json.loads(product["specs"])
        used_keys.update(specs)
        used_values.update(v for v in specs.values() if isinstance(v, str))

    for key in sorted(used_keys - set(i18n.SPEC_KEYS)):
        fail(problems, "SPEC_KEYS: untranslated spec key in use: %r" % key)

    # Values may stay untranslated, but only if they contain nothing but
    # numbers, units and codes. Anything with a real word must be translated.
    for value in sorted(used_values - set(i18n.SPEC_VALUES)):
        leftover = untranslated_tokens(value)
        if leftover:
            fail(
                problems,
                "SPEC_VALUES: untranslated spec value in use: %r (English: %s)"
                % (value, ", ".join(leftover)),
            )

    if verbose:
        print("  spec keys in use: %d, translated: %d" % (
            len(used_keys), len(used_keys & set(i18n.SPEC_KEYS))))
        print("  spec values in use: %d, translated: %d" % (
            len(used_values), len(used_values & set(i18n.SPEC_VALUES))))


def sample_args(template):
    """Plausible values for each placeholder, honouring %s vs %d.

    The kind matters: a %d placeholder refuses a str, so a value pool cannot be
    used blindly.
    """
    out = []
    for index, kind in enumerate(re.findall(r"%[sd]", template)):
        if kind == "%d":
            out.append(8 + index)
        else:
            out.append(["email", "price", "0.01", "a, b"][index % 4])
    return tuple(out)


def check_validation_templates(problems):
    """Every template must render and be recovered by the matcher.

    This is the test that matters for the validation layer: a translation can
    look fine in the table and still be unreachable if the pattern fails to
    capture the interpolated values.
    """
    for template, entry in i18n.VALIDATION_MESSAGES.items():
        try:
            rendered = template % sample_args(template)
        except (TypeError, ValueError) as exc:
            fail(problems, "VALIDATION_MESSAGES: %r does not render (%s)" % (template, exc))
            continue

        english_slots = len(re.findall(r"%[sd]", template))
        for lang in ("ar", "ku"):
            translation = entry.get(lang)
            if not translation:
                fail(problems, "VALIDATION_MESSAGES[%r]: no %s entry" % (template, lang))
                continue
            if len(re.findall(r"%[sd]", translation)) != english_slots:
                fail(
                    problems,
                    "VALIDATION_MESSAGES[%r][%s]: %d placeholders, English has %d"
                    % (template, lang, len(re.findall(r"%[sd]", translation)), english_slots),
                )
            got = i18n.validation_message(lang, rendered)
            if got == rendered:
                fail(
                    problems,
                    "VALIDATION_MESSAGES[%r][%s]: matcher did not translate %r"
                    % (template, lang, rendered),
                )
            elif english_slots and not all(
                str(a) in got for a in sample_args(template) if isinstance(a, str) and a
            ):
                fail(
                    problems,
                    "VALIDATION_MESSAGES[%r][%s]: interpolated value lost in %r"
                    % (template, lang, got),
                )


def main():
    # The tables are Arabic/Kurdish; a cp1252 console would raise mid-report.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    verbose = "-v" in sys.argv
    problems = []
    check_duplicate_keys(problems)
    check_products(problems)
    check_categories(problems)
    check_scripts(problems)
    check_embedded_latin(problems)
    check_spec_coverage(problems, verbose)
    check_validation_templates(problems)

    print("products seeded: %d, translated: %d" % (len(seed_products()), len(i18n.PRODUCTS)))
    print("categories: %d" % len(i18n.CATEGORY_NAMES))
    print("spec keys: %d, spec values: %d" % (len(i18n.SPEC_KEYS), len(i18n.SPEC_VALUES)))
    print("errors: %d, statuses: %d, payment methods: %d" % (
        len(i18n.ERRORS), len(i18n.ORDER_STATUSES), len(i18n.PAYMENT_METHODS)))
    for lang in ("ar", "ku"):
        missing = [n for n, e in i18n.PRODUCTS.items() if not e.get(lang)]
        if missing:
            fail(problems, "PRODUCTS: %d products have no %s entry: %s" % (len(missing), lang, missing[:5]))

    if problems:
        print("\n%d problem(s):" % len(problems))
        for problem in problems:
            print("  - %s" % problem)
        return 1
    print("\nOK - backend i18n tables are consistent with seed_data.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
