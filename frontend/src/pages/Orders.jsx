import { useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { api } from "../api";

export default function Orders() {
  const { token, user } = useAuth();
  const [orders, setOrders] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    api
      .getOrders(token)
      .then(setOrders)
      .catch((e) => setError(e.message || "Failed to load orders."));
  }, [token]);

  if (!token || !user) return <Navigate to="/login" replace />;

  return (
    <div className="page container">
      <h1 className="page-title">My Orders</h1>
      {error && <div className="notice error">{error}</div>}
      {!orders && !error && <div className="notice">Loading your orders…</div>}
      {orders && orders.length === 0 && (
        <div className="empty-state">
          <p>You have no orders yet.</p>
          <Link to="/products" className="btn btn-primary">Start Shopping</Link>
        </div>
      )}
      <div className="orders-list">
        {orders?.map((o) => (
          <div className="order-card" key={o.id}>
            <div className="order-head">
              <div>
                <strong>Order #{o.id}</strong>
                <span className="order-date">{new Date(o.createdAt).toLocaleString()}</span>
              </div>
              <span className={`order-status ${o.status.toLowerCase()}`}>{o.status}</span>
            </div>
            <div className="order-items">
              {o.items.map((it) => (
                <div className="order-item" key={it.product_id}>
                  <img src={it.image} alt="" width="44" height="44" />
                  <span className="order-item-name">{it.name}</span>
                  <span>{it.quantity} × ${Number(it.price).toFixed(2)}</span>
                </div>
              ))}
            </div>
            <div className="order-foot">
              <span>Total</span>
              <strong>${Number(o.total).toFixed(2)}</strong>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}