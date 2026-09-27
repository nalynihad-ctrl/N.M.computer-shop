import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { useLanguage } from "../context/LanguageContext";
import { api } from "../api";

export default function Register() {
  const { t } = useLanguage();
  const [form, setForm] = useState({ name: "", email: "", password: "", confirm: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const { user, signIn } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();

  if (user) return <Navigate to="/profile" replace />;

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    if (form.password !== form.confirm) {
      setError(t("register.mismatch"));
      return;
    }
    setBusy(true);
    setError("");
    try {
      const data = await api.register({
        name: form.name,
        email: form.email,
        password: form.password,
      });
      signIn(data.user, data.token);
      toast.success(t("toast.accountCreated"));
      navigate("/profile");
    } catch (err) {
      setError(err.message || t("register.failed"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="page container auth-center">
      <form className="auth-card" onSubmit={submit}>
        <h1>{t("register.title")}</h1>
        <p className="muted">{t("register.subtitle")}</p>
        {error && <div className="notice error">{error}</div>}
        <label className="field">
          <span>{t("field.fullName")}</span>
          <input
            className="input"
            required
            value={form.name}
            onChange={set("name")}
            placeholder={t("placeholder.name")}
          />
        </label>
        <label className="field">
          <span>{t("field.email")}</span>
          <input
            className="input"
            type="email"
            required
            value={form.email}
            onChange={set("email")}
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
            minLength="4"
            value={form.password}
            onChange={set("password")}
            placeholder={t("register.passwordHint")}
          />
        </label>
        <label className="field">
          <span>{t("field.confirmPassword")}</span>
          <input
            className="input"
            type="password"
            required
            value={form.confirm}
            onChange={set("confirm")}
            placeholder={t("register.repeatPassword")}
          />
        </label>
        <button className="btn btn-primary block" disabled={busy}>
          {busy ? t("register.submitting") : t("register.submit")}
        </button>
        <p className="muted center">
          {t("register.haveAccount")} <Link to="/login">{t("login.title")}</Link>
        </p>
      </form>
    </div>
  );
}
