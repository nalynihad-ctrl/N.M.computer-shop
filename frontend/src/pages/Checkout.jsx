import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useCart } from "../context/CartContext";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { useLanguage } from "../context/LanguageContext";
import { api } from "../api";

const FREE_SHIPPING_THRESHOLD = 100;
const SHIPPING_RATE = 9.99;

// `code` is the canonical English value the API accepts and validates, so it is
// what gets submitted; the shopper only ever sees the translated label.
const PAYMENT_METHODS = [
  { code: "Cash on Delivery", label: "payment.cod", desc: "payment.codDesc" },
  { code: "Card Payment", label: "payment.card", desc: "payment.cardDesc" },
];

export default function Checkout() {
  const { items, clearCart } = useCart();
  const { user, token } = useAuth();
  const toast = useToast();
  const { language, t, formatPrice } = useLanguage();

  const [form, setForm] = useState({
    fullName: user?.name || "",
    phone: user?.phone || "",
    email: user?.email || "",
    address: user?.address || "",
    city: user?.city || "",
    country: user?.country || "",
    paymentMethod: PAYMENT_METHODS[0].code,
  });
  const [placing, setPlacing] = useState(false);
  const [placed, setPlaced] = useState(null);
  // Same reason as the cart page: the summary has to name the products in the
  // active language, which means re-reading them by id.
  const [products, setProducts] = useState({});

  const ids = useMemo(() => items.map((i) => i.productId), [items]);
  const idsKey = ids.join(",");

  useEffect(() => {
    if (!ids.length) {
      setProducts({});
      return undefined;
    }
    let alive = true;
    api
      .getProductsByIds(ids)
      .then((rows) => {
        if (!alive) return;
        const map = {};
        for (const row of rows) map[row.id] = row;
        setProducts(map);
      })
      .catch(() => {});
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [idsKey, language]);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const lines = useMemo(
    () =>
      items.map((item) => {
        const fresh = products[item.productId];
        return {
          ...item,
          name: fresh ? fresh.name : item.name,
          price: fresh ? fresh.price : item.price,
        };
      }),
    [items, products]
  );
  const subtotal = lines.reduce((sum, line) => sum + line.price * line.quantity, 0);

  const shipping = subtotal >= FREE_SHIPPING_THRESHOLD ? 0 : SHIPPING_RATE;
  const discount = 0;
  const total = subtotal + shipping - discount;

  const placeOrder = async (e) => {
    e.preventDefault();
    if (items.length === 0) return;
    setPlacing(true);
    try {
      // Only ids and quantities are sent: the server re-prices the order from
      // its own catalogue, so a stale or edited client price cannot affect it.
      const result = await api.checkout(
        {
          ...form,
          items: lines.map((i) => ({ productId: i.productId, quantity: i.quantity })),
        },
        token || undefined
      );
      clearCart();
      setPlaced(result);
      window.scrollTo(0, 0);
    } catch (err) {
      // The API already returns this message in the active language.
      toast.error(err.message || t("checkout.failed"));
    } finally {
      setPlacing(false);
    }
  };

  if (placed) {
    return (
      <div className="page container empty-state">
        <div className="success-icon">✓</div>
        <h1>{t("checkout.successTitle")}</h1>
        <p>{t("checkout.successBody", { orderId: placed.orderId })}</p>
        <p className="muted">
          {t("checkout.successMeta", {
            method: placed.paymentMethod,
            total: formatPrice(placed.total),
          })}
        </p>
        <div className="success-actions">
          <Link to={token ? "/orders" : "/products"} className="btn btn-primary">
            {token ? t("checkout.viewOrders") : t("cart.continueShopping")}
          </Link>
          <Link to="/" className="btn btn-ghost">{t("checkout.backHome")}</Link>
        </div>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="page container empty-state">
        <h1>{t("cart.empty")}</h1>
        <Link to="/products" className="btn btn-primary">
          {t("cart.continueShopping")}
        </Link>
      </div>
    );
  }

  return (
    <div className="page container">
      <h1 className="page-title">{t("checkout.title")}</h1>
      <form className="checkout-layout" onSubmit={placeOrder}>
        <div className="checkout-form">
          <section>
            <h2>{t("checkout.customerInfo")}</h2>
            <div className="form-grid">
              <label className="field span2">
                <span>{t("field.fullName")}</span>
                <input
                  className="input"
                  required
                  value={form.fullName}
                  onChange={set("fullName")}
                  placeholder={t("placeholder.name")}
                />
              </label>
              <label className="field">
                <span>{t("field.phone")}</span>
                <input
                  className="input"
                  required
                  value={form.phone}
                  onChange={set("phone")}
                  placeholder="+1 555 000 1234"
                  dir="ltr"
                />
              </label>
              <label className="field">
                <span>{t("field.email")}</span>
                <input
                  className="input"
                  type="email"
                  required
                  value={form.email}
                  onChange={set("email")}
                  placeholder="john@example.com"
                  dir="ltr"
                />
              </label>
              <label className="field span2">
                <span>{t("field.address")}</span>
                <input
                  className="input"
                  required
                  value={form.address}
                  onChange={set("address")}
                  placeholder={t("placeholder.address")}
                />
              </label>
              <label className="field">
                <span>{t("field.city")}</span>
                <input
                  className="input"
                  required
                  value={form.city}
                  onChange={set("city")}
                  placeholder={t("placeholder.city")}
                />
              </label>
              <label className="field">
                <span>{t("field.country")}</span>
                <input
                  className="input"
                  required
                  value={form.country}
                  onChange={set("country")}
                  placeholder={t("placeholder.country")}
                />
              </label>
            </div>
          </section>

          <section>
            <h2>{t("checkout.paymentMethod")}</h2>
            <div className="payment-options">
              {PAYMENT_METHODS.map((method) => (
                <label className="payment-option" key={method.code}>
                  <input
                    type="radio"
                    name="payment"
                    checked={form.paymentMethod === method.code}
                    onChange={() =>
                      setForm((f) => ({ ...f, paymentMethod: method.code }))
                    }
                  />
                  <span>
                    <strong>{t(method.label)}</strong>
                    <small>{t(method.desc)}</small>
                  </span>
                </label>
              ))}
            </div>
          </section>
        </div>

        <aside className="cart-summary">
          <h3>{t("cart.summary")}</h3>
          {lines.map((i) => (
            <div className="summary-line" key={i.productId}>
              <span>
                {i.quantity} × {i.name}
              </span>
              <span>{formatPrice(i.price * i.quantity)}</span>
            </div>
          ))}
          <div className="summary-row">
            <span>{t("cart.subtotal")}</span>
            <span>{formatPrice(subtotal)}</span>
          </div>
          <div className="summary-row">
            <span>{t("cart.shipping")}</span>
            <span>{shipping === 0 ? t("common.free") : formatPrice(shipping)}</span>
          </div>
          <div className="summary-row">
            <span>{t("cart.discount")}</span>
            <span>{formatPrice(discount)}</span>
          </div>
          <div className="summary-row total">
            <span>{t("cart.total")}</span>
            <span>{formatPrice(total)}</span>
          </div>
          <button type="submit" className="btn btn-accent block" disabled={placing}>
            {placing ? t("checkout.placing") : t("checkout.placeOrder")}
          </button>
          <Link to="/cart" className="btn btn-ghost block">{t("checkout.backToCart")}</Link>
          <p className="muted small">{t("checkout.termsNote")}</p>
        </aside>
      </form>
    </div>
  );
}
