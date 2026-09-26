import { Link } from "react-router-dom";
import { X } from "@phosphor-icons/react";
import { useCart } from "../context/CartContext";
import { useToast } from "../context/ToastContext";

const FREE_SHIPPING_THRESHOLD = 100;
const SHIPPING_RATE = 9.99;

export default function Cart() {
  const { items, subtotal, changeQuantity, removeItem, clearCart } = useCart();
  const toast = useToast();

  if (items.length === 0) {
    return (
      <div className="page container empty-state">
        <h1>Your cart is empty.</h1>
        <p className="muted">Add some products before checking out.</p>
        <Link to="/products" className="btn btn-primary">Continue Shopping</Link>
      </div>
    );
  }

  const shipping = subtotal >= FREE_SHIPPING_THRESHOLD ? 0 : SHIPPING_RATE;
  const discount = 0;
  const total = subtotal + shipping - discount;

  return (
    <div className="page container">
      <h1 className="page-title">Shopping Cart</h1>
      <div className="cart-layout">
        <div className="cart-items">
          {items.map((i) => (
            <div className="cart-item" key={i.productId}>
              <Link to={`/products/${i.productId}`} className="cart-item-image">
                <img src={i.image} alt={i.name} />
              </Link>
              <div className="cart-item-info">
                <Link to={`/products/${i.productId}`} className="cart-item-name">{i.name}</Link>
                <span className="cart-item-brand">{i.brand}</span>
                <span className="cart-item-price">${i.price.toFixed(2)} each</span>
              </div>
              <div className="qty-selector">
                <button onClick={() => changeQuantity(i.productId, -1)} aria-label="Decrease quantity">−</button>
                <span>{i.quantity}</span>
                <button onClick={() => changeQuantity(i.productId, 1)} aria-label="Increase quantity">+</button>
              </div>
              <div className="cart-item-total">${(i.price * i.quantity).toFixed(2)}</div>
              <button
                className="btn-icon remove"
                onClick={() => {
                  removeItem(i.productId);
                  toast.success(`${i.name} removed from your cart.`);
                }}
                aria-label={`Remove ${i.name}`}
              >
                <X size={16} weight="light" />
              </button>
            </div>
          ))}
          <button className="btn btn-ghost btn-sm clear-all" onClick={clearCart}>
            Clear cart
          </button>
        </div>

        <aside className="cart-summary">
          <h3>Order Summary</h3>
          <div className="summary-row"><span>Subtotal</span><span>${subtotal.toFixed(2)}</span></div>
          <div className="summary-row"><span>Shipping</span><span>{shipping === 0 ? "Free" : `$${shipping.toFixed(2)}`}</span></div>
          <div className="summary-row"><span>Discount</span><span>${discount.toFixed(2)}</span></div>
          <div className="summary-row total"><span>Total</span><span>${total.toFixed(2)}</span></div>
          {shipping > 0 && (
            <p className="muted small">Add ${(FREE_SHIPPING_THRESHOLD - subtotal).toFixed(2)} more for free shipping.</p>
          )}
          <Link to="/checkout" className="btn btn-accent block">Proceed to Checkout</Link>
          <Link to="/products" className="btn btn-ghost block">Continue Shopping</Link>
        </aside>
      </div>
    </div>
  );
}