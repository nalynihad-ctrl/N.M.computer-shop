import { Link } from "react-router-dom";
import { useLanguage } from "../context/LanguageContext";

export default function Footer() {
  const { t } = useLanguage();

  return (
    <footer className="footer">
      <div className="footer-grid container">
        <div className="footer-col footer-brand-col">
          <div className="footer-brand">
            <img src="/uploads/logo.svg" alt="Naly,munib logo" />
            <strong>Naly<span>,munib</span></strong>
          </div>
          <span className="footer-blurb">{t("footer.blurb")}</span>
        </div>
        <div className="footer-col">
          <h4>{t("footer.shop")}</h4>
          <Link to="/products">{t("footer.allProducts")}</Link>
          <Link to="/products">{t("footer.categories")}</Link>
          <Link to="/products?sort=newest">{t("footer.newArrivals")}</Link>
          <Link to="/products?sort=price_asc">{t("footer.deals")}</Link>
        </div>
        <div className="footer-col">
          <h4>{t("footer.customerService")}</h4>
          <Link to="/contact">{t("footer.contactUs")}</Link>
          <Link to="/shipping">{t("footer.shipping")}</Link>
          <Link to="/returns">{t("footer.returns")}</Link>
          <Link to="/warranty">{t("footer.warranty")}</Link>
          <Link to="/faq">{t("footer.faq")}</Link>
        </div>
        <div className="footer-col">
          <h4>{t("footer.company")}</h4>
          <Link to="/about">{t("footer.aboutUs")}</Link>
          <Link to="/privacy-policy">{t("footer.privacy")}</Link>
          <Link to="/terms">{t("footer.terms")}</Link>
        </div>
        <div className="footer-col footer-contact">
          {/* Address, phone and email are contact details rather than copy, so
              they are shown as written rather than translated. */}
          <h4>{t("footer.contact")}</h4>
          <span dir="ltr">+1 (312) 847-1928</span>
          <span dir="ltr">support@nalymunib.shop</span>
          <span>411 Wabash Ave, Suite 3, Chicago, IL 60611</span>
        </div>
      </div>
      <div className="footer-bottom container">
        {t("footer.copyright", { year: new Date().getFullYear() })}
      </div>
    </footer>
  );
}
