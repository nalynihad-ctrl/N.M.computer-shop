import { Link, useNavigate } from "react-router-dom";
import { useCart } from "../context/CartContext";
import { useToast } from "../context/ToastContext";
import { useLanguage } from "../context/LanguageContext";
import RatingStars from "./RatingStars";

export default function ProductCard({ product }) {
  const { addItem } = useCart();
  const toast = useToast();
  const navigate = useNavigate();
  const { t, formatPrice } = useLanguage();
  const outOfStock = product.stock <= 0;

  const handleAdd = (e) => {
    e.preventDefault();
    e.stopPropagation();
    addItem(product);
    toast.success(t("toast.addedToCart", { name: product.name }));
  };

  const handleBuyNow = (e) => {
    e.preventDefault();
    e.stopPropagation();
    addItem(product);
    navigate("/cart");
  };

  return (
    <Link to={`/products/${product.id}`} className="product-card">
      <div className="card-media">
        <img src={product.image} alt={product.name} loading="lazy" />
        {product.discount > 0 && (
          <span className="badge-discount">-{product.discount}%</span>
        )}
        {outOfStock && <span className="badge-out">{t("product.outOfStock")}</span>}
      </div>
      <div className="card-body">
        {/* categoryName is the translated label; `category` stays the canonical
            key and is what links and filters are built from. */}
        <span className="card-category">{product.categoryName || product.category}</span>
        <h3 className="card-name">{product.name}</h3>
        <span className="card-brand">{product.brand}</span>
        <div className="card-rating">
          <RatingStars rating={product.rating} showValue />
          <span className={`stock ${outOfStock ? "empty" : ""}`}>
            {outOfStock
              ? t("product.soldOut")
              : t("product.unitsAvailable", { count: product.stock })}
          </span>
        </div>
        <div className="card-price">
          <span className="price">{formatPrice(product.price)}</span>
          {product.oldPrice > product.price && (
            <span className="old-price">{formatPrice(product.oldPrice)}</span>
          )}
        </div>
        <div className="card-actions">
          <button className="btn btn-primary btn-sm" onClick={handleAdd} disabled={outOfStock}>
            {t("product.addToCart")}
          </button>
          <button
            className="btn btn-ghost btn-sm"
            onClick={handleBuyNow}
            disabled={outOfStock}
          >
            {t("product.buyNow")}
          </button>
        </div>
      </div>
    </Link>
  );
}
