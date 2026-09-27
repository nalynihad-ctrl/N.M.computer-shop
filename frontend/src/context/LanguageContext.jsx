import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { createTranslator, preloadCatalogs, formatPrice, formatDateTime, LANGUAGE_STORAGE_KEY } from "../i18n";
import { setApiLanguage } from "../api";

const LanguageContext = createContext(null);
const KEY = LANGUAGE_STORAGE_KEY;
const DEFAULT_CODE = "en";

export const LANGUAGES = [
  { code: "en", label: "English", native: "English", dir: "ltr" },
  { code: "ar", label: "Arabic", native: "\u0627\u0644\u0639\u0631\u0628\u064a\u0629", dir: "rtl" },
  { code: "ku", label: "Kurdish", native: "\u06a9\u0648\u0631\u062f\u06cc", dir: "rtl" },
];

const BY_CODE = Object.create(null);
for (const item of LANGUAGES) BY_CODE[item.code] = item;

function resolveLanguage(code) {
  return typeof code === "string" && Object.prototype.hasOwnProperty.call(BY_CODE, code)
    ? BY_CODE[code]
    : null;
}

// Re-exported so components can reach the key through the context module they
// already import, while api.js reads the single definition from i18n.
export { LANGUAGE_STORAGE_KEY };

export function getLanguage(code) {
  return resolveLanguage(code) || BY_CODE[DEFAULT_CODE];
}

function getInitialLanguage() {
  try {
    const saved = localStorage.getItem(KEY);
    if (resolveLanguage(saved)) return saved;
  } catch {
    /* ignore storage errors */
  }
  return DEFAULT_CODE;
}

// Start fetching the split catalogs as soon as this module is evaluated, not
// from inside an effect. An effect runs after the first paint, so a returning
// Arabic or Kurdish visitor would get a frame of English before their catalog
// arrived; module scope moves the wait to before the first render.
const catalogsPending = preloadCatalogs();

export function LanguageProvider({ children }) {
  const [language, setLanguage] = useState(getInitialLanguage);
  // Whether the catalog for the current language is actually in memory. The
  // translator falls back to English until it is, which is correct but not what
  // the visitor should be left looking at, so this flag forces one re-render
  // when the load lands and the correct text takes over.
  const [catalogsReady, setCatalogsReady] = useState(false);

  useEffect(() => {
    let active = true;
    catalogsPending.then(() => {
      if (active) setCatalogsReady(true);
    });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    const current = getLanguage(language);
    const root = document.documentElement;
    root.setAttribute("lang", current.code);
    root.setAttribute("dir", current.dir);
    try {
      localStorage.setItem(KEY, current.code);
    } catch {
      /* ignore quota errors */
    }
  }, [language]);

  // The document title, description and Open Graph tags are part of the
  // interface, not just the page: a shared link preview, a bookmark and a
  // search result all read them, so they follow the language too. The static
  // values in index.html stay as the English default for the very first paint,
  // before any catalog has loaded.
  useEffect(() => {
    if (!catalogsReady) return;
    const setMeta = (selector, attr, value) => {
      const el = document.head.querySelector(selector);
      if (el) el.setAttribute(attr, value);
    };
    document.title = "Naly,Munib | PC Parts & Gaming";
    setMeta('meta[name="description"]', "content", "PC Parts & Gaming shop");
    setMeta('meta[property="og:title"]', "content", "Naly,Munib");
    setMeta('meta[property="og:description"]', "content", "PC Parts & Gaming shop");
  }, [language, catalogsReady]);

  const changeLanguage = useCallback((code) => {
    if (resolveLanguage(code)) setLanguage(code);
  }, []);

  const current = getLanguage(language);

  const value = useMemo(
    () => ({
      language: current.code,
      dir: current.dir,
      languages: LANGUAGES,
      setLanguage: changeLanguage,
      // Re-created per language so that every consumer re-renders when the
      // language changes, and so a stale closure can never survive a switch.
      // `catalogsReady` is in the deps because before it flips the translator
      // below would have been built with the catalog still missing.
      t: createTranslator(current.code),
      formatPrice,
      formatDateTime: (value) => formatDateTime(value, current.code),
    }),
    // The API layer is updated here rather than in the effect above, because
    // React runs a child's effect before its parent's. A page that refetches on
    // a language change does so from its own effect, which fires first, so
    // setting this in the parent's effect would still be one step behind and
    // every refetch would ask for the previous language. Computing the context
    // value happens during render, before any child effect runs.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [current.code, current.dir, catalogsReady, changeLanguage]
  );

  setApiLanguage(current.code);

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

// Used only if a component renders outside the provider (a test harness, or a
// future refactor that mounts a page on its own). English is resolved
// synchronously by the translator, so this is a fully working fallback rather
// than a stub that echoes keys back at the user.
const FALLBACK = {
  language: DEFAULT_CODE,
  dir: "ltr",
  languages: LANGUAGES,
  setLanguage: () => {},
  t: createTranslator(DEFAULT_CODE),
  formatPrice,
  formatDateTime: (value) => formatDateTime(value, DEFAULT_CODE),
};

export function useLanguage() {
  return useContext(LanguageContext) || FALLBACK;
}
