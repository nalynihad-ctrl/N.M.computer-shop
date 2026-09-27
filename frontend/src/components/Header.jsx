import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { MagnifyingGlass, Moon, ShoppingCart, Sun, User } from "@phosphor-icons/react";
import { useCart } from "../context/CartContext";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";
import { useLanguage } from "../context/LanguageContext";
import LanguageSwitcher from "./LanguageSwitcher";

export default function Header() {
  const { count } = useCart();
  const { user } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { t } = useLanguage();
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
          aria-label={t("a11y.menu")}
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
            placeholder={t("search.placeholder")}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            aria-label={t("a11y.searchProducts")}
          />
          <button type="submit" className="btn-icon" aria-label={t("a11y.search")}>
            <MagnifyingGlass size={18} weight="light" />
          </button>
        </form>

        <nav className="header-actions">
          <LanguageSwitcher />
          <button
            className="btn-icon theme-toggle"
            aria-label={theme === "dark" ? t("a11y.switchToLight") : t("a11y.switchToDark")}
            title={theme === "dark" ? t("a11y.switchToLight") : t("a11y.switchToDark")}
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
            aria-label={t("a11y.toggleSearch")}
            onClick={() => setSearchOpen((v) => !v)}
          >
            <MagnifyingGlass size={20} weight="light" />
          </button>
          <Link to={profileLink} className="btn-icon" aria-label={t("a11y.account")}>
            <User size={20} weight="light" />
          </Link>
          <Link
            to="/cart"
            className="btn-icon cart-btn"
            aria-label={t("a11y.cartWithCount", { count })}
          >
            <ShoppingCart size={20} weight="light" />
            {count > 0 && <span className="cart-badge">{count}</span>}
          </Link>
        </nav>
      </div>

      {menuOpen && (
        <nav className="mobile-menu container">
          <div className="lang-mobile-slot">
            <LanguageSwitcher />
          </div>
          <Link to="/" onClick={() => setMenuOpen(false)}>{t("nav.home")}</Link>
          <Link to="/products" onClick={() => setMenuOpen(false)}>{t("nav.allProducts")}</Link>
          <Link to="/cart" onClick={() => setMenuOpen(false)}>{t("nav.cart")}</Link>
          <Link to={profileLink} onClick={() => setMenuOpen(false)}>{t("nav.account")}</Link>
          <Link to="/orders" onClick={() => setMenuOpen(false)}>{t("nav.orders")}</Link>
          <Link to="/about" onClick={() => setMenuOpen(false)}>{t("nav.about")}</Link>
          <Link to="/contact" onClick={() => setMenuOpen(false)}>{t("nav.contact")}</Link>
        </nav>
      )}
    </header>
  );
}