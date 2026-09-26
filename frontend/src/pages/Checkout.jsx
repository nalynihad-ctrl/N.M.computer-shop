import { useState } from "react";
import { Link } from "react-router-dom";
import { useCart } from "../context/CartContext";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { api } from "../api";

const FREE_SHIPPING_THRESHOLD = 100;
const SHIPPING_RATE = 9.99;

export default function Checkout() {
  const { items, subtotal, clearCart } = useCart();
  const { user, token } = useAuth();
  const toast = useToast();

  const [form, setForm] = useState({
    fullName: user?.name || "",
    phone: user?.phone || "",
    email: user?.email || "",
    address: user?.address || "",
    city: user?.city || "",
    country: user?.country || "",
    paymentMethod: "Cash on Delivery",
  });
  const [placing, setPlacing] = useState(false);
  const [placed, setPlaced] = useState(null);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const shipping = subtotal >= FREE_SHIPPING_THRESHOLD ? 0 : SHIPPING_RATE;
  const discount = 0;
  const total = subtotal + shipping - discount;

  const placeOrder = async (e) => {
    e.preventDefault();
    if (items.length === 0) return;
    setPlacing(true);
    try {
      const result = await api.checkout(
        {
          ...form,
          items: items.map((i) => ({ productId: i.productId, quantity: i.quantity })),
        },
        token || undefined
      );
      clearCart();
      setPlaced(result);
      window.scrollTo(0, 0);
    } catch (err) {
      toast.error(err.message || "Checkout failed. Please try again.");
    } finally {
      setPlacing(false);
    }
  };

  if (placed) {
    return (
      <div className="page container empty-state">
        <div className="success-icon">✓</div>
        <h1>Order placed!</h1>
        <p>Your order <strong>#{placed.orderId}</strong> has been received and is being processed.</p>
        <p className="muted">Payment method: {form.paymentMethod} · Total: ${placed.total.toFixed(2)}</p>
        <div className="success-actions">
          <Link to={token ? "/orders" : "/products"} className="btn btn-primary">
            {token ? "View My Orders" : "Continue Shopping"}
          </Link>
          <Link to="/" className="btn btn-ghost">Back to Home</Link>
        </div>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="page container empty-state">
        <h1>Your cart is empty.</h1>
        <Link to="/products" className="btn btn-primary">Continue Shopping</Link>
      </div>
    );
  }

  return (
    <div className="page container">
      <h1 className="page-title">Checkout</h1>
      <form className="checkout-layout" onSubmit={placeOrder}>
        <div className="checkout-form">
          <section>
            <h2>Customer Information</h2>
            <div className="form-grid">
              <label className="field span2">
                <span>Full name</span>
                <input className="input" required value={form.fullName} onChange={set("fullName")} placeholder="Alex Rivera" />
              </label>
              <label className="field">
                <span>Phone</span>
                <input className="input" required value={form.phone} onChange={set("phone")} placeholder="+1 555 000 1234" />
              </label>
              <label className="field">
                <span>Email</span>
                <input className="input" type="email" required value={form.email} onChange={set("email")} placeholder="john@example.com" />
              </label>
              <label className="field span2">
                <span>Address</span>
                <input className="input" required value={form.address} onChange={set("address")} placeholder="411 Wabash Ave" />
              </label>
              <label className="field">
                <span>City</span>
                <input className="input" required value={form.city} onChange={set("city")} placeholder="Chicago" />
              </label>
              <label className="field">
                <span>Country / Region</span>
                <input className="input" required value={form.country} onChange={set("country")} placeholder="United States" />
              </label>
            </div>
          </section>

          <section>
            <h2>Payment Method</h2>
            <div className="payment-options">
              <label className="payment-option">
                <input type="radio" name="payment" checked={form.paymentMethod === "Cash on Delivery"} onChange={() => setForm((f) => ({ ...f, paymentMethod: "Cash on Delivery" }))} />
                <span>
                  <strong>Cash on Delivery</strong>
                  <small>Pay when your order arrives.</small>
                </span>
              </label>
              <label className="payment-option">
                <input type="radio" name="payment" checked={form.paymentMethod === "Card Payment"} onChange={() => setForm((f) => ({ ...f, paymentMethod: "Card Payment" }))} />
                <span>
                  <strong>Card Payment</strong>
                  <small>Online payment integration coming soon.</small>
                </span>
              </label>
            </div>
          </section>
        </div>

        <aside className="cart-summary">
          <h3>Order Summary</h3>
          {items.map((i) => (
            <div className="summary-line" key={i.productId}>
              <span>{i.quantity} × {i.name}</span>
              <span>${(i.price * i.quantity).toFixed(2)}</span>
            </div>
          ))}
          <div className="summary-row"><span>Subtotal</span><span>${subtotal.toFixed(2)}</span></div>
          <div className="summary-row"><span>Shipping</span><span>{shipping === 0 ? "Free" : `$${shipping.toFixed(2)}`}</span></div>
          <div className="summary-row"><span>Discount</span><span>${discount.toFixed(2)}</span></div>
          <div className="summary-row total"><span>Total</span><span>${total.toFixed(2)}</span></div>
          <button type="submit" className="btn btn-accent block" disabled={placing}>
            {placing ? "Placing order…" : "Place Order"}
          </button>
          <Link to="/cart" className="btn btn-ghost block">Back to Cart</Link>
          <p className="muted small">By placing this order you agree to our terms &amp; conditions.</p>
        </aside>
      </form>
    </div>
  );
}