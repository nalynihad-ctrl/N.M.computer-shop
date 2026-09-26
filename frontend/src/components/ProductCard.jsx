import { Link, useNavigate } from "react-router-dom";
import { useCart } from "../context/CartContext";
import { useToast } from "../context/ToastContext";
import RatingStars from "./RatingStars";

export default function ProductCard({ product }) {
  const { addItem } = useCart();
  const toast = useToast();
  const navigate = useNavigate();
  const outOfStock = product.stock <= 0;

  const handleAdd = (e) => {
    e.preventDefault();
    e.stopPropagation();
    addItem(product);
    toast.success(`${product.name} added to your cart.`);
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
        {outOfStock && <span className="badge-out">Out of stock</span>}
      </div>
      <div className="card-body">
        <span className="card-category">{product.category}</span>
        <h3 className="card-name">{product.name}</h3>
        <span className="card-brand">{product.brand}</span>
        <div className="card-rating">
          <RatingStars rating={product.rating} showValue />
          <span className={`stock ${outOfStock ? "empty" : ""}`}>
            {outOfStock ? "Sold out" : `${product.stock} in stock`}
          </span>
        </div>
        <div className="card-price">
          <span className="price">${product.price.toFixed(2)}</span>
          {product.oldPrice > product.price && (
            <span className="old-price">${product.oldPrice.toFixed(2)}</span>
          )}
        </div>
        <div className="card-actions">
          <button className="btn btn-primary btn-sm" onClick={handleAdd} disabled={outOfStock}>
            Add to Cart
          </button>
          <button
            className="btn btn-ghost btn-sm"
            onClick={handleBuyNow}
            disabled={outOfStock}
          >
            Buy Now
          </button>
        </div>
      </div>
    </Link>
  );
}