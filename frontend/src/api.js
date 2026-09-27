import { LANGUAGE_STORAGE_KEY } from "./i18n";

const API = "/api";

// Set by the language provider on every switch. It is cached here purely to save
// a storage read per request; the localStorage fallback below is what makes the
// value correct even for a request that is issued before the provider's effect
// has run (React runs a child's effect before its parent's, so a page that
// fetches on mount really can beat it), and it keeps this module free of any
// dependency on React.
let activeLang = null;

export function setApiLanguage(code) {
  activeLang = code || null;
}

function currentLang() {
  if (activeLang) return activeLang;
  try {
    return localStorage.getItem(LANGUAGE_STORAGE_KEY) || "en";
  } catch {
    return "en";
  }
}

async function handle(res) {
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = new Error(data.error || `Request failed (${res.status})`);
    err.status = res.status;
    throw err;
  }
  return data;
}

function qs(params) {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params || {})) {
    if (v !== undefined && v !== null && v !== "") sp.set(k, v);
  }
  const s = sp.toString();
  return s ? `?${s}` : "";
}

// Every request carries the active language twice over: as ?lang=, which the
// backend treats as authoritative, and as Accept-Language, which is what any
// cache or proxy in front of the API will vary on. Sending both means a language
// switch changes the response body and the cache key together, instead of a
// stale Arabic or Kurdish payload being replayed for an English visitor.
function langQuery(extra) {
  const sp = new URLSearchParams();
  sp.set("lang", currentLang());
  for (const [k, v] of Object.entries(extra || {})) {
    if (v !== undefined && v !== null && v !== "") sp.set(k, v);
  }
  return `?${sp.toString()}`;
}

function langHeaders(token) {
  const lang = currentLang();
  return {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    "Accept-Language": lang,
  };
}

export const api = {
  // Stage 5 audit fix - `get` never sent the Authorization header, so every
  // token-protected GET (me, orders, order detail) went out unauthenticated and
  // came back 401. The bearer token is now forwarded, matching `post`.
  get: (path, params, token) =>
    fetch(`${API}${path}${langQuery(params)}`, {
      headers: langHeaders(token),
    }).then(handle),
  post: (path, body, token) =>
    fetch(`${API}${path}${langQuery()}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...langHeaders(token),
      },
      body: JSON.stringify(body || {}),
    }).then(handle),

  getProducts: (params) => api.get("/products", params),
  getProduct: (id) => api.get(`/products/${id}`),
  getCategories: () => api.get("/categories"),
  getBrands: () => api.get("/brands"),
  // The cart keeps product ids, so it asks for its own lines back by id to get
  // the current product data in the active language. `name` in a stored cart
  // line is only ever a placeholder for the first paint; the cart re-reads it.
  getProductsByIds: (ids) =>
    api.get("/products", ids && ids.length ? { ids: ids.join(",") } : null),

  register: (data) => api.post("/auth/register", data),
  login: (data) => api.post("/auth/login", data),
  me: (token) => api.get("/auth/me", null, token).catch(() => null),
  logout: (token) => api.post("/auth/logout", {}, token),

  checkout: (data, token) => api.post("/checkout", data, token),
  getOrders: (token) => api.get("/orders", null, token),
  getOrder: (id, token) => api.get(`/orders/${id}`, null, token),
};
