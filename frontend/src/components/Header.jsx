import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { MagnifyingGlass, Moon, ShoppingCart, Sun, User } from "@phosphor-icons/react";
import { useCart } from "../context/CartContext";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";

export default function Header() {
  const { count } = useCart();
  const { user } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);

  const submitSearch = (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    navigate(`/products?search=${encodeURIComponent(query.trim())}`);
    setMenuOpen(false);
    setSearchOpen(false);
    setQuery("");
  };

  const profileLink = user ? "/profile" : "/login";

  return (
    <header className="header">
      <div className="header-row container">
        <button
          className="hamburger"
          aria-label="Menu"
          onClick={() => setMenuOpen((v) => !v)}
        >
          <span />
          <span />
          <span />
        </button>

        <Link to="/" className="brand" onClick={() => setMenuOpen(false)}>
          <img src="/uploads/logo.svg" alt="Naly,munib logo" />
          <span className="brand-name">Naly<span>,munib</span></span>
        </Link>

        <form className={`search-form ${searchOpen ? "open" : ""}`} onSubmit={submitSearch}>
          <input
            type="search"
            placeholder="Search products, brands, categories…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            aria-label="Search products"
          />
          <button type="submit" className="btn-icon" aria-label="Search">
            <MagnifyingGlass size={18} weight="light" />
          </button>
        </form>

        <nav className="header-actions">
          <button
            className="btn-icon theme-toggle"
            aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
            title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
            onClick={toggleTheme}
          >
            {theme === "dark" ? (
              <Sun size={20} weight="light" />
            ) : (
              <Moon size={20} weight="light" />
            )}
          </button>
          <button
            className="btn-icon mobile-search-only"
            aria-label="Toggle search"
            onClick={() => setSearchOpen((v) => !v)}
          >
            <MagnifyingGlass size={20} weight="light" />
          </button>
          <Link to={profileLink} className="btn-icon" aria-label="Account">
            <User size={20} weight="light" />
          </Link>
          <Link to="/cart" className="btn-icon cart-btn" aria-label={`Cart, ${count} items`}>
            <ShoppingCart size={20} weight="light" />
            {count > 0 && <span className="cart-badge">{count}</span>}
          </Link>
        </nav>
      </div>

      {menuOpen && (
        <nav className="mobile-menu container">
          <Link to="/" onClick={() => setMenuOpen(false)}>Home</Link>
          <Link to="/products" onClick={() => setMenuOpen(false)}>All Products</Link>
          <Link to="/cart" onClick={() => setMenuOpen(false)}>Shopping Cart</Link>
          <Link to={profileLink} onClick={() => setMenuOpen(false)}>My Account</Link>
          <Link to="/orders" onClick={() => setMenuOpen(false)}>My Orders</Link>
          <Link to="/about" onClick={() => setMenuOpen(false)}>About Us</Link>
          <Link to="/contact" onClick={() => setMenuOpen(false)}>Contact</Link>
        </nav>
      )}
    </header>
  );
}