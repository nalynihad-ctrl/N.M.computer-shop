const API = "/api";

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

export const api = {
  // Stage 5 audit fix - `get` never sent the Authorization header, so every
  // token-protected GET (me, orders, order detail) went out unauthenticated and
  // came back 401. The bearer token is now forwarded, matching `post`.
  get: (path, params, token) =>
    fetch(`${API}${path}${qs(params)}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    }).then(handle),
  post: (path, body, token) =>
    fetch(`${API}${path}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(body || {}),
    }).then(handle),

  getProducts: (params) => api.get("/products", params),
  getProduct: (id) => api.get(`/products/${id}`),
  getCategories: () => api.get("/categories"),
  getBrands: () => api.get("/brands"),

  register: (data) => api.post("/auth/register", data),
  login: (data) => api.post("/auth/login", data),
  me: (token) => api.get("/auth/me", null, token).catch(() => null),
  logout: (token) => api.post("/auth/logout", {}, token),

  checkout: (data, token) => api.post("/checkout", data, token),
  getOrders: (token) => api.get("/orders", null, token),
  getOrder: (id, token) => api.get(`/orders/${id}`, null, token),
};
