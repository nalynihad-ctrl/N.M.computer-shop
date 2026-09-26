import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { api } from "../api";

export default function Register() {
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
      setError("Passwords do not match.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const data = await api.register({ name: form.name, email: form.email, password: form.password });
      signIn(data.user, data.token);
      toast.success("Account created. Welcome!");
      navigate("/profile");
    } catch (err) {
      setError(err.message || "Registration failed.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="page container auth-center">
      <form className="auth-card" onSubmit={submit}>
        <h1>Create Account</h1>
        <p className="muted">Create your Naly,munib account to track orders and check out faster.</p>
        {error && <div className="notice error">{error}</div>}
        <label className="field">
          <span>Full name</span>
          <input className="input" required value={form.name} onChange={set("name")} placeholder="Alex Rivera" />
        </label>
        <label className="field">
          <span>Email</span>
          <input className="input" type="email" required value={form.email} onChange={set("email")} placeholder="you@example.com" />
        </label>
        <label className="field">
          <span>Password</span>
          <input className="input" type="password" required minLength="4" value={form.password} onChange={set("password")} placeholder="At least 4 characters" />
        </label>
        <label className="field">
          <span>Confirm password</span>
          <input className="input" type="password" required value={form.confirm} onChange={set("confirm")} placeholder="Repeat password" />
        </label>
        <button className="btn btn-primary block" disabled={busy}>
          {busy ? "Creating account…" : "Register"}
        </button>
        <p className="muted center">
          Already have an account? <Link to="/login">Login</Link>
        </p>
      </form>
    </div>
  );
}