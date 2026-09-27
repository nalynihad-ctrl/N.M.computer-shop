import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { useLanguage } from "../context/LanguageContext";
import { api } from "../api";

export default function Login() {
  const { t } = useLanguage();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const { user, signIn } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();

  if (user) return <Navigate to="/profile" replace />;

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const data = await api.login({ email, password });
      signIn(data.user, data.token);
      toast.success(t("toast.welcomeBack", { name: data.user.name }));
      navigate("/profile");
    } catch (err) {
      // The API returns its reason already translated, so it is shown as-is and
      // only replaced if there was no body to read.
      setError(err.message || t("login.failed"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="page container auth-center">
      <form className="auth-card" onSubmit={submit}>
        <h1>{t("login.title")}</h1>
        <p className="muted">{t("login.subtitle")}</p>
        {error && <div className="notice error">{error}</div>}
        <label className="field">
          <span>{t("field.email")}</span>
          <input
            className="input"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            dir="ltr"
          />
        </label>
        <label className="field">
          <span>{t("field.password")}</span>
          <input
            className="input"
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
          />
        </label>
        <button className="btn btn-primary block" disabled={busy}>
          {busy ? t("login.submitting") : t("login.submit")}
        </button>
        <p className="muted center">
          {t("login.noAccount")} <Link to="/register">{t("login.createOne")}</Link>
        </p>
      </form>
    </div>
  );
}
