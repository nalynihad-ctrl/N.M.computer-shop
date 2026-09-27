// Catalog parity + script-range check. Run: node frontend/tools/check-catalogs.mjs
import { readdirSync, readFileSync } from "node:fs";
import { join, relative } from "node:path";
import { fileURLToPath } from "node:url";
import en from "../src/i18n/en.js";
import ar from "../src/i18n/ar.js";
import ku from "../src/i18n/ku.js";
import { createTranslator, preloadCatalogs } from "../src/i18n/index.js";

const PLURAL_FORMS = new Set([
  "zero", "one", "two", "few", "many", "other",
]);

const catalogs = { en, ar, ku };
const problems = [];

function walk(node, path, out) {
  if (Array.isArray(node)) {
    out.push(path);
    node.forEach((v, i) => {
      if (v !== null && typeof v === "object") walk(v, `${path}[${i}]`, out);
    });
    return;
  }
  if (node === null || typeof node !== "object") {
    out.push(path);
    return;
  }
  // A group whose every key is a CLDR plural category is a plural group; its
  // per-form children are allowed to differ between locales, so the shape check
  // stops at the group itself.
  const keys = Object.keys(node);
  if (keys.length && keys.every((k) => PLURAL_FORMS.has(k))) {
    out.push(path);
    return;
  }
  for (const [k, v] of Object.entries(node)) walk(v, path ? `${path}.${k}` : k, out);
}

const shapes = {};
for (const [code, cat] of Object.entries(catalogs)) {
  const out = [];
  walk(cat, "", out);
  shapes[code] = new Set(out);
}

const base = shapes.en;
for (const code of ["ar", "ku"]) {
  for (const key of base) {
    if (!shapes[code].has(key)) problems.push(`${code}: missing key "${key}"`);
  }
  for (const key of shapes[code]) {
    if (!base.has(key)) problems.push(`${code}: extra key "${key}" not in en`);
  }
}

// Every plural group must supply each form its locale actually selects, and the
// real translator must be able to find those forms by the path it builds at
// runtime. Deriving the groups from the catalogs (rather than listing them here)
// means a new plural group is covered the moment it is added, and checking the
// actual `t()` call is what catches a resolver/catalog path mismatch - a group
// can be complete and still be unreachable if the two disagree on the spelling.
const PROBE_COUNTS = [0, 1, 2, 3, 11, 100];
const LOCALES = { en: "en-US", ar: "ar-IQ", ku: "ckb-IQ" };

function collectPluralGroups(catalog, node = catalog, path = "", out = []) {
  if (Array.isArray(node) || node === null || typeof node !== "object") return out;
  const keys = Object.keys(node);
  if (keys.length && keys.every((k) => PLURAL_FORMS.has(k))) {
    out.push([path, node]);
    return out;
  }
  for (const [k, v] of Object.entries(node)) {
    collectPluralGroups(catalog, v, path ? `${path}.${k}` : k, out);
  }
  return out;
}

const groups = collectPluralGroups(en);
if (!groups.length) problems.push("en: no plural groups found at all");

function lookup(catalog, path) {
  let node = catalog;
  for (const part of path.split(".")) {
    if (node === null || typeof node !== "object") return undefined;
    node = node[part];
    if (node === undefined) return undefined;
  }
  return node;
}

for (const [code, cat] of Object.entries(catalogs)) {
  for (const [name] of groups) {
    // Each locale is checked against its *own* group, not the English one.
    const group = lookup(cat, name);
    if (typeof group !== "object" || group === null) {
      problems.push(`${code}: ${name} is not a plural group`);
      continue;
    }
    // English only ever selects one/other, so the extra forms would be dead
    // weight; Arabic and Kurdish must each cover all six CLDR categories.
    const required = code === "en" ? ["one", "other"] : [...PLURAL_FORMS];
    for (const form of required) {
      if (typeof group[form] !== "string") problems.push(`${code}: ${name} missing form "${form}"`);
    }
    if (code === "en") {
      for (const form of Object.keys(group)) {
        if (!["one", "other"].includes(form)) {
          problems.push(`${code}: ${name} has unneeded form "${form}"`);
        }
      }
    }
  }
}

// The catalog shape is only half the contract; the other half is that `t()` can
// actually resolve it. Resolve every plural group through the real translator at
// a spread of counts chosen to hit every CLDR form, in every language, and
// require the rendered string to be exactly the form this count selects.
await preloadCatalogs();
const fill = (s, params) =>
  s.replace(/\{(\w+)\}/g, (m, k) =>
    Object.prototype.hasOwnProperty.call(params, k) ? String(params[k]) : m);

for (const [code, locale] of Object.entries(LOCALES)) {
  const t = createTranslator(code);
  for (const [name] of groups) {
    const group = lookup(catalogs[code], name) || {};
    for (const count of PROBE_COUNTS) {
      let form;
      try {
        form = new Intl.PluralRules(locale).select(count);
      } catch {
        form = new Intl.PluralRules("en").select(count);
      }
      if (typeof group[form] !== "string") continue;
      const expected = fill(group[form], { count });
      const rendered = t(name, { count });
      if (rendered !== expected) {
        problems.push(
          `${code}: t("${name}", {count:${count}}) rendered ${JSON.stringify(rendered)}, ` +
          `expected the "${form}" form ${JSON.stringify(expected)}`
        );
      }
    }
  }
}

// Flag characters from scripts that have no business in any of these catalogs.
const scriptRe = /[\u0400-\u04FF\u4E00-\u9FFF\u3040-\u30FF\u0600-\u06FF]/gu;
const arRe = /[\u0600-\u06FF]/u;
const kuRe = /[\u0600-\u06FF\u0698\u06A9\u06AF\u06CC\u06D5]/u;
for (const [code, cat] of Object.entries(catalogs)) {
  const text = JSON.stringify(cat);
  const stray = [];
  for (const [k, v] of Object.entries(cat)) void k, void v;
  // Scan per string so we can report a path.
  const scan = (node, path) => {
    if (typeof node === "string") {
      for (const ch of node.matchAll(scriptRe)) {
        const isAr = arRe.test(ch[0]);
        const isKu = kuRe.test(ch[0]);
        const ok = (code === "ar" && isAr) || (code === "ku" && isKu) || (code === "en" && !isAr && !isKu);
        if (!ok) stray.push(`${path}: ${ch[0]} (U+${ch[0].codePointAt(0).toString(16).toUpperCase()})`);
      }
    } else if (Array.isArray(node)) {
      node.forEach((v, i) => scan(v, `${path}[${i}]`));
    } else if (node && typeof node === "object") {
      for (const [k, v] of Object.entries(node)) scan(v, path ? `${path}.${k}` : k);
    }
  };
  scan(cat, "");
  // CJK / Cyrillic anywhere is always wrong.
  for (const m of text.matchAll(/[\u0400-\u04FF\u4E00-\u9FFF\u3040-\u30FF]/gu)) {
    stray.push(`(anywhere) ${m[0]} U+${m[0].codePointAt(0).toString(16).toUpperCase()}`);
  }
  for (const s of new Set(stray)) problems.push(`${code}: stray script char ${s}`);
}

// Every placeholder in a translation must also exist in the English source.
const phRe = /\{(\w+)\}/g;
const placeholders = (s) => (typeof s === "string" ? [...s.matchAll(phRe)].map((m) => m[1]).sort() : []);
const collect = (node, path, out) => {
  if (typeof node === "string") out.push([path, node]);
  else if (Array.isArray(node)) node.forEach((v, i) => collect(v, `${path}[${i}]`, out));
  else if (node && typeof node === "object") {
    for (const [k, v] of Object.entries(node)) collect(v, path ? `${path}.${k}` : k, out);
  }
};
const enStrings = [];
collect(en, "", enStrings);
const enPh = new Map(enStrings.map(([p, s]) => [p, placeholders(s)]));

// Placeholders: a translation may use fewer of the source's placeholders than
// the English string does (idiomatic Arabic and Kurdish singular forms use the
// grammatical singular - "one product" - instead of repeating the numeral), but
// it must never invent one the source does not have, because that would render
// a literal "{foo}" into the page.
for (const code of ["ar", "ku"]) {
  const mine = [];
  collect(catalogs[code], "", mine);
  for (const [p, s] of mine) {
    if (!enPh.has(p)) continue;
    const allowed = enPh.get(p);
    for (const name of placeholders(s)) {
      if (!allowed.includes(name)) problems.push(`${code}: "${p}" invents placeholder {${name}}`);
    }
  }
}

// No string may still be identical to the English source (untranslated copy).
for (const code of ["ar", "ku"]) {
  const mine = [];
  collect(catalogs[code], "", mine);
  for (const [p, s] of mine) {
    const src = enStrings.find(([q]) => q === p);
    if (src && src[1] === s && /[A-Za-z]{3,}/.test(s)) {
      problems.push(`${code}: "${p}" is still the English string: ${s.slice(0, 60)}`);
    }
  }
}

// Every `t("...")` key used in the source must resolve in every language.
// `t()` falls back to English and finally to returning the key itself, so a typo
// does not throw - it quietly renders "cart.summry" on the page. With this many
// call sites that is the most likely way a translation change goes unnoticed.
const SRC = fileURLToPath(new URL("../src/", import.meta.url));
function sourceFiles(dir) {
  const out = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) out.push(...sourceFiles(full));
    else if (/\.(jsx|js)$/.test(entry.name)) out.push(full);
  }
  return out;
}

const staticKey = /\bt\(\s*"([a-zA-Z0-9_.]+)"/g;
for (const file of sourceFiles(SRC)) {
  const rel = relative(SRC, file).replace(/\\/g, "/");
  if (rel === "i18n/en.js") continue;
  const text = readFileSync(file, "utf8");
  for (const m of text.matchAll(staticKey)) {
    const key = m[1];
    for (const code of ["en", "ar", "ku"]) {
      if (lookup(catalogs[code], key) === undefined) {
        problems.push(`${code}: t("${key}") in ${rel} does not exist`);
      }
    }
  }
}

// Keys built from an interpolated value, e.g. t(`contact.topic.${topic}`), cannot
// be enumerated from the source, so the prefix and every leaf are listed here.
// A new dynamic call site has to be added below to be covered.
const DYNAMIC_KEYS = [
  ["contact.topic.", ["order", "shipping", "returns", "advice", "other"]],
];
for (const [prefix, leaves] of DYNAMIC_KEYS) {
  for (const leaf of leaves) {
    for (const code of ["en", "ar", "ku"]) {
      if (lookup(catalogs[code], prefix + leaf) === undefined) {
        problems.push(`${code}: t("${prefix}${leaf}") does not exist`);
      }
    }
  }
}

// Cross-boundary contract: the enums the API stores are the keys the frontend
// renders from. Nothing in the type system ties them together - a rename on
// either side compiles, deploys, and only shows up as a raw "Pending" on an
// order page. So the backend's canonical values are read straight out of its
// source and matched against this app.
const BACKEND = fileURLToPath(new URL("../../backend/i18n.py", import.meta.url));
const backSrc = readFileSync(BACKEND, "utf8");

function backendDict(name) {
  const start = backSrc.indexOf(`${name} = {`);
  if (start < 0) throw new Error(`cannot find ${name} in backend/i18n.py`);
  const open = backSrc.indexOf("{", start);
  let depth = 0;
  for (let i = open; i < backSrc.length; i += 1) {
    if (backSrc[i] === "{") depth += 1;
    else if (backSrc[i] === "}") {
      depth -= 1;
      if (depth === 0) {
        return [...backSrc.slice(open, i + 1).matchAll(/"([^"]+)":\s*\{/g)].map((m) => m[1]);
      }
    }
  }
  throw new Error(`unterminated ${name} in backend/i18n.py`);
}

const slug = (s) => s.toLowerCase();

// Every status the API can store needs a translated label and a stylesheet rule,
// both keyed by the lower-cased canonical value.
const statuses = backendDict("ORDER_STATUSES");
const css = readFileSync(fileURLToPath(new URL("../src/index.css", import.meta.url)), "utf8");
for (const status of statuses) {
  for (const code of ["en", "ar", "ku"]) {
    if (lookup(catalogs[code], `status.${slug(status)}`) === undefined) {
      problems.push(`${code}: status "${status}" has no status.${slug(status)} label`);
    }
  }
  // A substring test would pass for ".order-status.refundedXX", so the selector
  // has to end at a real boundary.
  if (!new RegExp(`\\.order-status\\.${slug(status)}(?![-\\w])`).test(css)) {
    problems.push(`css: no .order-status.${slug(status)} rule for backend status "${status}"`);
  }
}
// The reverse: a label or rule for a status the API can never send is dead code.
for (const key of Object.keys(en.status)) {
  if (!statuses.some((s) => slug(s) === key)) problems.push(`en: status.${key} matches no backend status`);
}

// Payment methods: the frontend submits the canonical value, so the pair of
// {code, label} entries in Checkout has to match the backend's accepted set
// exactly - one extra code is a 400 at checkout, one missing is a dead option.
const payments = backendDict("PAYMENT_METHODS");
const checkout = readFileSync(fileURLToPath(new URL("../src/pages/Checkout.jsx", import.meta.url)), "utf8");
const submitted = [...checkout.matchAll(/code:\s*"([^"]+)"/g)].map((m) => m[1]);
for (const code of submitted) {
  if (!payments.includes(code)) {
    problems.push(`contract: Checkout submits payment code "${code}" the API does not accept`);
  }
}
for (const code of payments) {
  if (!submitted.includes(code)) {
    problems.push(`contract: API accepts payment code "${code}" but Checkout never offers it`);
  }
}

if (problems.length) {
  console.error(`FAIL - ${problems.length} problem(s):`);
  for (const p of problems) console.error("  - " + p);
  process.exit(1);
}
console.log(
  `OK - en/ar/ku catalogs match: keys, plural forms, placeholders, scripts, ` +
  `${statuses.length} statuses, ${payments.length} payment codes, ` +
  `${sourceFiles(SRC).length} source files.`
);
