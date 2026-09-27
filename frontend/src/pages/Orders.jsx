import { useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import { api } from "../api";

// The API returns both `status` (already translated) and `statusCode` (the
// stored enum, e.g. "Pending"). Presentation keys off the code, never the
// label: the label changes with the language, and keying the stylesheet off it
// would drop the colour the moment the store is viewed in Arabic. The code is
// lower-cased into the CSS slug the stylesheet defines, and the visible text
// comes from this app's own catalog so it stays consistent with the rest of the
// interface. An unrecognised code falls back to the server's own translation
// rather than printing a raw enum value at the shopper.
function statusSlug(order) {
  return String(order.statusCode || order.status || "").toLowerCase();
}

function StatusPill({ order, t }) {
  const slug = statusSlug(order);
  const key = t(`status.${slug}`);
  const label = key === `status.${slug}` ? order.status : key;
  return <span className={`order-status ${slug}`}>{label}</span>;
}

export default function Orders() {
  const { language, t, formatPrice, formatDateTime } = useLanguage();
  const { token, user } = useAuth();
  const [orders, setOrders] = useState(null);
  const [error, setError] = useState("");

  // Order status, payment method and item names all arrive translated, so the
  // list is re-read whenever the language changes.
  useEffect(() => {
    if (!token) return;
    let alive = true;
    api
      .getOrders(token)
      .then((data) => alive && setOrders(data))
      .catch((e) => alive && setError(e.message || t("orders.failed")));
    return () => {
      alive = false;
    };
  }, [token, language, t]);

  if (!token || !user) return <Navigate to="/login" replace />;

  return (
    <div className="page container">
      <h1 className="page-title">{t("orders.title")}</h1>
      {error && <div className="notice error">{error}</div>}
      {!orders && !error && <div className="notice">{t("orders.loading")}</div>}
      {orders && orders.length === 0 && (
        <div className="empty-state">
          <p>{t("orders.empty")}</p>
          <Link to="/products" className="btn btn-primary">
            {t("orders.startShopping")}
          </Link>
        </div>
      )}
      <div className="orders-list">
        {orders?.map((o) => (
          <div className="order-card" key={o.id}>
            <div className="order-head">
              <div>
                <strong>{t("orders.number", { id: o.id })}</strong>
                <span className="order-date">{formatDateTime(o.createdAt)}</span>
              </div>
              <StatusPill order={o} t={t} />
            </div>
            <div className="order-items">
              {o.items.map((it) => (
                <div className="order-item" key={it.product_id}>
                  <img src={it.image} alt="" width="44" height="44" />
                  <span className="order-item-name">{it.name}</span>
                  <span>
                    {it.quantity} × {formatPrice(it.price)}
                  </span>
                </div>
              ))}
            </div>
            <div className="order-foot">
              <span>{t("orders.total")}</span>
              <strong>{formatPrice(o.total)}</strong>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
