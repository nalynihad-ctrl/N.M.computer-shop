import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { useLanguage } from "../context/LanguageContext";
import { api } from "../api";

export default function Profile() {
  const { t } = useLanguage();
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
    toast.success(t("toast.loggedOut"));
    navigate("/");
  };

  return (
    <div className="page container">
      <h1 className="page-title">{t("profile.title")}</h1>
      <div className="profile-layout">
        <section className="profile-card">
          <div className="avatar">{user.name.charAt(0).toUpperCase()}</div>
          <h2>{user.name}</h2>
          <p className="muted" dir="ltr">{user.email}</p>
          {/* These are the customer's own details, not catalogue copy, so only
              the field labels are translated. */}
          <div className="profile-fields">
            <div>
              <span>{t("profile.phone")}</span>
              <strong dir="ltr">{user.phone || "-"}</strong>
            </div>
            <div>
              <span>{t("profile.address")}</span>
              <strong>{user.address || "-"}</strong>
            </div>
            <div>
              <span>{t("profile.city")}</span>
              <strong>{user.city || "-"}</strong>
            </div>
            <div>
              <span>{t("profile.country")}</span>
              <strong>{user.country || "-"}</strong>
            </div>
          </div>
        </section>
        <aside className="profile-actions">
          <Link to="/orders" className="menu-link">{t("profile.orders")}</Link>
          <Link to="/" className="menu-link">{t("profile.continueShopping")}</Link>
          <button onClick={logout} className="btn btn-danger">{t("profile.logout")}</button>
        </aside>
      </div>
    </div>
  );
}
