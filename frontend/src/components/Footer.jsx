import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-grid container">
        <div className="footer-col footer-brand-col">
          <div className="footer-brand">
            <img src="/uploads/logo.svg" alt="Naly,munib logo" />
            <strong>Naly<span>,munib</span></strong>
          </div>
          <span className="footer-blurb">
            PC parts and gaming hardware for people who actually build. Ships fast,
            tested by people who wrench on their own rigs.
          </span>
        </div>
        <div className="footer-col">
          <h4>Shop</h4>
          <Link to="/products">All Products</Link>
          <Link to="/products">Categories</Link>
          <Link to="/products?sort=newest">New Arrivals</Link>
          <Link to="/products?sort=price_asc">Deals</Link>
        </div>
        <div className="footer-col">
          <h4>Customer Service</h4>
          <Link to="/contact">Contact Us</Link>
          <Link to="/shipping">Shipping</Link>
          <Link to="/returns">Returns</Link>
          <Link to="/warranty">Warranty</Link>
          <Link to="/faq">FAQ</Link>
        </div>
        <div className="footer-col">
          <h4>Company</h4>
          <Link to="/about">About Us</Link>
          <Link to="/privacy-policy">Privacy Policy</Link>
          <Link to="/terms">Terms &amp; Conditions</Link>
        </div>
        <div className="footer-col footer-contact">
          <h4>Contact</h4>
          <span>+1 (312) 847-1928</span>
          <span>support@nalymunib.shop</span>
          <span>411 Wabash Ave, Suite 3, Chicago, IL 60611</span>
        </div>
      </div>
      <div className="footer-bottom container">
        © {new Date().getFullYear()} Naly,munib. All rights reserved.
      </div>
    </footer>
  );
}