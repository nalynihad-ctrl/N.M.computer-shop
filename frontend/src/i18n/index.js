/**
 * Minimal, dependency-free message translator.
 *
 * The project has no i18n library on purpose: the whole language layer is a
 * React context, and adding a framework for ~200 strings would be more moving
 * parts than the feature itself. This module supplies the three things a
 * translator actually needs and nothing more.
 *
 *   1. Dotted-path lookup        t("cart.summary")
 *   2. {placeholder} interpolation t("toast.addedToCart", { name })
 *   3. Locale-aware plurals       t("toolbar.productCount", { count })
 *
 * The lookup order for a key is deliberate and is what makes a partial
 * translation safe rather than broken:
 *
 *   active catalog, locale plural form -> active catalog, "other"
 *     -> English catalog, same path   -> English catalog, "other"
 *     -> the key itself
 *
 * So a gap in the Arabic or Kurdish catalog shows English text for that one
 * string, never `cart.summary` on screen, and a genuinely untranslated feature
 * still degrades predictably.
 */

// Extensions are written out explicitly so this module is valid ESM to a plain
// Node loader as well as to the bundler; the catalog checker imports it
// directly, outside Vite.
import en from "./en.js";

/**
 * Where the chosen language is persisted.
 *
 * This lives in the i18n module rather than in LanguageContext so that the
 * plain data layer (api.js) can read the current language without importing
 * React or the context that owns it. The context re-exports it for components.
 */
export const LANGUAGE_STORAGE_KEY = "computer_shop_language";

const CATALOGS = {
  en,
  ar: () => import("./ar.js"),
  ku: () => import("./ku.js"),
};

// Synchronously required copies, populated on first use of each language. The
// catalogs are tiny, and a dynamic import per render would be far worse than
// holding one reference, so the first switch to a language awaits the module
// and re-renders. `loaded` is also what lets us fall back to English
// synchronously before a catalog has arrived.
const RESOLVED = { en };

let loadPromise = null;

/** Kick off loading every catalog; resolves once all are available. */
export function preloadCatalogs() {
  if (loadPromise) return loadPromise;
  loadPromise = Promise.all(
    Object.keys(CATALOGS).map(async (code) => {
      if (RESOLVED[code]) return;
      const load = CATALOGS[code];
      const mod = typeof load === "function" ? await load() : load;
      RESOLVED[code] = mod.default || mod;
    })
  ).then(() => undefined);
  return loadPromise;
}

function lookup(catalog, path) {
  if (!catalog) return undefined;
  let node = catalog;
  for (const part of path.split(".")) {
    if (node === null || typeof node !== "object") return undefined;
    node = node[part];
    if (node === undefined) return undefined;
  }
  return node;
}

/**
 * Pick the plural sub-form. Arabic distinguishes zero/one/two/few/many/other, so
 * a hard-coded "_one"/"_other" pair would give Arabic the wrong agreement for
 * every count except 1 and 0. If the locale is unknown to the runtime (an old
 * browser, or an unusual one such as the Sorani locale code) Intl falls back
 * to the English rules, which is why every catalog still has to be valid when
 * read with the "one"/"other" split.
 */
function pluralForm(locale, count) {
  try {
    return new Intl.PluralRules(locale).select(count);
  } catch {
    return new Intl.PluralRules("en").select(count);
  }
}

function interpolate(template, params) {
  if (!params) return template;
  // Only the named {placeholder} form is substituted. A positional pass would
  // be a trap here: the catalogs contain literal prices such as "$9.99" and
  // "$100", which a $1-style rewrite would happily eat.
  return template.replace(/\{(\w+)\}/g, (match, key) =>
    Object.prototype.hasOwnProperty.call(params, key) ? String(params[key]) : match
  );
}

/**
 * Build a translator bound to one language.
 *
 * @param {string} lang  language code, e.g. "ar"
 * @returns {(key: string, params?: object) => string}
 */
export function createTranslator(lang) {
  const active = RESOLVED[lang];

  return function t(key, params) {
    const count = params && typeof params.count === "number" ? params.count : null;
    const form = count === null ? null : pluralForm(lang, count);

    // Plural forms are nested under the key (home.productCount.one) rather than
    // suffixed onto it (home.productCount_one). The flat form is still accepted
    // as a second spelling so a hand-added catalog entry cannot silently fall
    // through to English.
    const candidates = [];
    if (form) {
      candidates.push(`${key}.${form}`);
      candidates.push(`${key}_${form}`);
    }
    candidates.push(key);
    if (form) {
      candidates.push(`${key}.other`);
      candidates.push(`${key}_other`);
    }

    for (const candidate of candidates) {
      const hit = lookup(active, candidate);
      // Arrays and objects are returned as-is so a component can pull a whole
      // localized list with one call, e.g. t("hero.banners") -> the four
      // banner records, or t("faq.qa") -> the question/answer pairs.
      if (hit !== undefined) return typeof hit === "string" ? interpolate(hit, params) : hit;
    }
    for (const candidate of candidates) {
      const hit = lookup(en, candidate);
      if (hit !== undefined) return typeof hit === "string" ? interpolate(hit, params) : hit;
    }
    return key;
  };
}

/**
 * Currency for a catalogue that is priced in US dollars.
 *
 * Deliberately pinned to the "en-US" number format regardless of the interface
 * language: the amount is the same dollars in every language, and letting an
 * Arabic locale format it would render the totals with different grouping (or
 * different digits) than the receipts, the order table and the database hold.
 */
export function formatPrice(amount) {
  return `$${Number(amount).toFixed(2)}`;
}

/** Locale-aware date/time for the order history. */
export function formatDateTime(value, lang) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value ?? "");
  const locales = { en: "en-US", ar: "ar-IQ", ku: "ckb-IQ" };
  try {
    return date.toLocaleString(locales[lang] || "en-US");
  } catch {
    return date.toLocaleString("en-US");
  }
}
