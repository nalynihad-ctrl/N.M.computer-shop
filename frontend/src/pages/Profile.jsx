import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { api } from "../api";

export default function Profile() {
  const { user, token, signOut } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();

  if (!token || !user) return <Navigate to="/login" replace />;

  const logout = async () => {
    try {
      await api.logout(token);
    } catch {
      /* ignore */
    }
    signOut();
    toast.success("You have been logged out.");
    navigate("/");
  };

  return (
    <div className="page container">
      <h1 className="page-title">My Account</h1>
      <div className="profile-layout">
        <section className="profile-card">
          <div className="avatar">{user.name.charAt(0).toUpperCase()}</div>
          <h2>{user.name}</h2>
          <p className="muted">{user.email}</p>
          <div className="profile-fields">
            <div><span>Phone</span><strong>{user.phone || "-"}</strong></div>
            <div><span>Address</span><strong>{user.address || "-"}</strong></div>
            <div><span>City</span><strong>{user.city || "-"}</strong></div>
            <div><span>Country</span><strong>{user.country || "-"}</strong></div>
          </div>
        </section>
        <aside className="profile-actions">
          <Link to="/orders" className="menu-link">My Orders →</Link>
          <Link to="/" className="menu-link">Continue Shopping →</Link>
          <button onClick={logout} className="btn btn-danger">Logout</button>
        </aside>
      </div>
    </div>
  );
}