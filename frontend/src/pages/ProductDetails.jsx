import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import ProductCard from "../components/ProductCard";
import RatingStars from "../components/RatingStars";
import { api } from "../api";
import { useCart } from "../context/CartContext";
import { useToast } from "../context/ToastContext";
import { useLanguage } from "../context/LanguageContext";

export default function ProductDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { addItem } = useCart();
  const toast = useToast();
  const { language, t, formatPrice } = useLanguage();

  const [product, setProduct] = useState(null);
  const [related, setRelated] = useState([]);
  const [qty, setQty] = useState(1);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  // The name, description and spec labels are all translated server-side, so
  // the request is repeated when the language changes. `id` is the product, and
  // the related-products query filters on the canonical category key.
  useEffect(() => {
    setLoading(true);
    setNotFound(false);
    setQty(1);
    let alive = true;
    api
      .getProduct(id)
      .then(async (p) => {
        if (!alive) return;
        setProduct(p);
        setQty(1);
        const r = await api.getProducts({ category: p.category, limit: 4 });
        if (alive) setRelated(r.filter((x) => x.id !== p.id).slice(0, 4));
      })
      .catch(() => alive && setNotFound(true))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [id, language]);

  if (loading) {
    return <div className="page container"><div className="skeleton-detail" /></div>;
  }

  if (notFound || !product) {
    return (
      <div className="page container empty-state">
        <p>{t("product.notFound")}</p>
        <Link to="/products" className="btn btn-primary">{t("product.backToProducts")}</Link>
      </div>
    );
  }

  const out = product.stock <= 0;
  // Link to the canonical key, label with the translated name.
  const categoryLabel = product.categoryName || product.category;

  const handleAdd = () => {
    addItem(product, qty);
    toast.success(t("toast.addedToCart", { name: product.name }));
  };

  const handleBuyNow = () => {
    addItem(product, qty);
    navigate("/cart");
  };

  return (
    <div className="page container">
      <nav className="breadcrumb">
        <Link to="/">{t("nav.home")}</Link>{" "}
        <Link to={`/category/${encodeURIComponent(product.category)}`}>{categoryLabel}</Link>{" "}
        <span>{product.name}</span>
      </nav>

      <div className="detail-layout">
        <div className="detail-gallery">
          <div className="detail-main-image">
            <img src={product.image} alt={product.name} />
            {product.discount > 0 && (
              <span className="badge-discount big">-{product.discount}%</span>
            )}
          </div>
        </div>

        <div className="detail-info">
          <span className="card-category">{product.brand} &middot; {categoryLabel}</span>
          <h1 className="detail-name">{product.name}</h1>
          <div className="detail-rating">
            <RatingStars rating={product.rating} showValue />
            <span className="stock-line">
              {out
                ? t("product.outOfStock")
                : t("product.unitsAvailable", { count: product.stock })}
            </span>
          </div>

          <div className="detail-price">
            <span className="price big">{formatPrice(product.price)}</span>
            {product.oldPrice > product.price && (
              <span className="old-price big">{formatPrice(product.oldPrice)}</span>
            )}
            {product.discount > 0 && (
              <span className="save">{t("product.save", { percent: product.discount })}</span>
            )}
          </div>

          <p className="detail-desc">{product.description}</p>

          <div className="detail-actions">
            <div className="qty-selector">
              <button
                onClick={() => setQty((q) => Math.max(1, q - 1))}
                aria-label={t("a11y.decreaseQuantity")}
              >
                &minus;
              </button>
              <span>{qty}</span>
              <button
                onClick={() => setQty((q) => Math.min(product.stock || 1, q + 1))}
                aria-label={t("a11y.increaseQuantity")}
              >
                +
              </button>
            </div>
            <button className="btn btn-primary" onClick={handleAdd} disabled={out}>
              {t("product.addToCart")}
            </button>
            <button className="btn btn-ghost" onClick={handleBuyNow} disabled={out}>
              {t("product.buyNow")}
            </button>
          </div>
        </div>
      </div>

      <section className="section">
        <h2 className="detail-subtitle">{t("product.specs")}</h2>
        <div className="specs-table">
          {/* Both halves of each row arrive translated from the API. */}
          {Object.entries(product.specs || {}).map(([k, v]) => (
            <div className="spec-row" key={k}>
              <span className="spec-key">{k}</span>
              <span className="spec-value">{v}</span>
            </div>
          ))}
        </div>
      </section>

      {related.length > 0 && (
        <section className="section">
          <div className="section-head">
            <h2>{t("product.related")}</h2>
          </div>
          <div className="product-grid">
            {related.map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
