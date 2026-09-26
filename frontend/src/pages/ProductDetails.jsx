import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import ProductCard from "../components/ProductCard";
import RatingStars from "../components/RatingStars";
import { api } from "../api";
import { useCart } from "../context/CartContext";
import { useToast } from "../context/ToastContext";

export default function ProductDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { addItem } = useCart();
  const toast = useToast();

  const [product, setProduct] = useState(null);
  const [related, setRelated] = useState([]);
  const [qty, setQty] = useState(1);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    setLoading(true);
    setNotFound(false);
    setQty(1);
    api
      .getProduct(id)
      .then(async (p) => {
        setProduct(p);
        setQty(1);
        api.getProducts({ category: p.category, limit: 4 }).then((r) => {
          setRelated(r.filter((x) => x.id !== p.id).slice(0, 4));
        }).catch(() => {});
      })
      .catch(() => setNotFound(true))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return <div className="page container"><div className="skeleton-detail" /></div>;
  }

  if (notFound || !product) {
    return (
      <div className="page container empty-state">
        <p>Product not found.</p>
        <Link to="/products" className="btn btn-primary">Back to products</Link>
      </div>
    );
  }

  const out = product.stock <= 0;

  const handleAdd = () => {
    addItem(product, qty);
    toast.success(`${product.name} added to your cart.`);
  };

  const handleBuyNow = () => {
    addItem(product, qty);
    navigate("/cart");
  };

  return (
    <div className="page container">
      <nav className="breadcrumb">
        <Link to="/">Home</Link> /{" "}
        <Link to={`/category/${encodeURIComponent(product.category)}`}>{product.category}</Link> /{" "}
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
          <span className="card-category">{product.brand} &middot; {product.category}</span>
          <h1 className="detail-name">{product.name}</h1>
          <div className="detail-rating">
            <RatingStars rating={product.rating} showValue />
            <span className="stock-line">{out ? "Out of stock" : `${product.stock} units available`}</span>
          </div>

          <div className="detail-price">
            <span className="price big">${product.price.toFixed(2)}</span>
            {product.oldPrice > product.price && (
              <span className="old-price big">${product.oldPrice.toFixed(2)}</span>
            )}
            {product.discount > 0 && <span className="save">Save {product.discount}%</span>}
          </div>

          <p className="detail-desc">{product.description}</p>

          <div className="detail-actions">
            <div className="qty-selector">
              <button onClick={() => setQty((q) => Math.max(1, q - 1))} aria-label="Decrease quantity">−</button>
              <span>{qty}</span>
              <button onClick={() => setQty((q) => Math.min(product.stock || 1, q + 1))} aria-label="Increase quantity">+</button>
            </div>
            <button className="btn btn-primary" onClick={handleAdd} disabled={out}>
              Add to Cart
            </button>
            <button className="btn btn-ghost" onClick={handleBuyNow} disabled={out}>
              Buy Now
            </button>
          </div>
        </div>
      </div>

      <section className="section">
        <h2 className="detail-subtitle">Technical Specifications</h2>
        <div className="specs-table">
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
            <h2>You may also like</h2>
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