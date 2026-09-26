import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="page container empty-state">
      <h1>404 - Page not found</h1>
      <p className="muted">The page you are looking for does not exist.</p>
      <Link to="/" className="btn btn-primary">Back to Home</Link>
    </div>
  );
}