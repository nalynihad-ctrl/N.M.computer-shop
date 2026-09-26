import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { api } from "../api";

export default function Login() {
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
      toast.success(`Welcome back, ${data.user.name}!`);
      navigate("/profile");
    } catch (err) {
      setError(err.message || "Login failed.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="page container auth-center">
      <form className="auth-card" onSubmit={submit}>
        <h1>Login</h1>
        <p className="muted">Access your account to view orders and checkout faster.</p>
        {error && <div className="notice error">{error}</div>}
        <label className="field">
          <span>Email</span>
          <input className="input" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" />
        </label>
        <label className="field">
          <span>Password</span>
          <input className="input" type="password" required value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" />
        </label>
        <button className="btn btn-primary block" disabled={busy}>
          {busy ? "Signing in…" : "Login"}
        </button>
        <p className="muted center">
          No account yet? <Link to="/register">Create one</Link>
        </p>
      </form>
    </div>
  );
}