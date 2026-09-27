import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { X } from "@phosphor-icons/react";
import { useCart } from "../context/CartContext";
import { useToast } from "../context/ToastContext";
import { useLanguage } from "../context/LanguageContext";
import { api } from "../api";

const FREE_SHIPPING_THRESHOLD = 100;
const SHIPPING_RATE = 9.99;

export default function Cart() {
  const { items, changeQuantity, removeItem, clearCart } = useCart();
  const toast = useToast();
  const { language, t, formatPrice } = useLanguage();

  // A stored cart line keeps the name it was added with, which would be the
  // language that happened to be active at the time. The ids are the durable
  // part, so the current product data - name, brand, image and price - is read
  // back for the active language and the snapshot is only a first-paint
  // placeholder. Without this, a cart built in English keeps English product
  // names after a switch to Arabic.
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
      // A failed refresh is not a reason to empty the cart; the stored snapshot
      // stays on screen instead.
      .catch(() => {});
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [idsKey, language]);

  // Prefer the refreshed product, fall back to the stored snapshot so a line
  // still renders if the product was removed or the request failed.
  const lines = useMemo(
    () =>
      items.map((item) => {
        const fresh = products[item.productId];
        return {
          ...item,
          name: fresh ? fresh.name : item.name,
          brand: fresh ? fresh.brand : item.brand,
          image: fresh ? fresh.image : item.image,
          price: fresh ? fresh.price : item.price,
          oldPrice: fresh ? fresh.oldPrice : item.oldPrice,
        };
      }),
    [items, products]
  );

  // Priced from the same merged lines the page displays, so a price that changed
  // since the item was added cannot disagree with the order summary beside it.
  const subtotal = useMemo(
    () => lines.reduce((sum, line) => sum + line.price * line.quantity, 0),
    [lines]
  );

  if (items.length === 0) {
    return (
      <div className="page container empty-state">
        <h1>{t("cart.empty")}</h1>
        <p className="muted">{t("cart.emptyHint")}</p>
        <Link to="/products" className="btn btn-primary">
          {t("cart.continueShopping")}
        </Link>
      </div>
    );
  }

  const shipping = subtotal >= FREE_SHIPPING_THRESHOLD ? 0 : SHIPPING_RATE;
  const discount = 0;
  const total = subtotal + shipping - discount;

  return (
    <div className="page container">
      <h1 className="page-title">{t("cart.title")}</h1>
      <div className="cart-layout">
        <div className="cart-items">
          {lines.map((i) => (
            <div className="cart-item" key={i.productId}>
              <Link to={`/products/${i.productId}`} className="cart-item-image">
                <img src={i.image} alt={i.name} />
              </Link>
              <div className="cart-item-info">
                <Link to={`/products/${i.productId}`} className="cart-item-name">
                  {i.name}
                </Link>
                <span className="cart-item-brand">{i.brand}</span>
                <span className="cart-item-price">
                  {t("cart.each", { price: formatPrice(i.price) })}
                </span>
              </div>
              <div className="qty-selector">
                <button
                  onClick={() => changeQuantity(i.productId, -1)}
                  aria-label={t("a11y.decreaseQuantity")}
                >
                  &minus;
                </button>
                <span>{i.quantity}</span>
                <button
                  onClick={() => changeQuantity(i.productId, 1)}
                  aria-label={t("a11y.increaseQuantity")}
                >
                  +
                </button>
              </div>
              <div className="cart-item-total">
                {formatPrice(i.price * i.quantity)}
              </div>
              <button
                className="btn-icon remove"
                onClick={() => {
                  removeItem(i.productId);
                  toast.success(t("toast.removedFromCart", { name: i.name }));
                }}
                aria-label={t("a11y.removeItem", { name: i.name })}
              >
                <X size={16} weight="light" />
              </button>
            </div>
          ))}
          <button className="btn btn-ghost btn-sm clear-all" onClick={clearCart}>
            {t("cart.clear")}
          </button>
        </div>

        <aside className="cart-summary">
          <h3>{t("cart.summary")}</h3>
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
          {shipping > 0 && (
            <p className="muted small">
              {t("cart.freeShippingHint", {
                amount: formatPrice(FREE_SHIPPING_THRESHOLD - subtotal),
              })}
            </p>
          )}
          <Link to="/checkout" className="btn btn-accent block">
            {t("cart.checkout")}
          </Link>
          <Link to="/products" className="btn btn-ghost block">
            {t("cart.continueShopping")}
          </Link>
        </aside>
      </div>
    </div>
  );
}
