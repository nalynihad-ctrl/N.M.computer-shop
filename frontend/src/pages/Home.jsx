import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import HeroSlider from "../components/HeroSlider";
import ProductCard from "../components/ProductCard";
import { api } from "../api";
import { useLanguage } from "../context/LanguageContext";

export default function Home() {
  const { language, t } = useLanguage();
  const [categories, setCategories] = useState([]);
  const [newArrivals, setNewArrivals] = useState([]);
  const [popular, setPopular] = useState([]);

  // Refetched on a language change: product names, descriptions, spec labels and
  // category names all arrive from the server already translated, so the results
  // in state are only correct for the language that produced them.
  useEffect(() => {
    let alive = true;
    api
      .getCategories()
      .then((data) => alive && setCategories(data))
      .catch(() => {});
    api
      .getProducts({ sort: "newest", limit: 8 })
      .then((data) => alive && setNewArrivals(data))
      .catch(() => {});
    api
      .getProducts({ sort: "popular", limit: 8 })
      .then((data) => alive && setPopular(data))
      .catch(() => {});
    return () => {
      alive = false;
    };
  }, [language]);

  return (
    <div className="home">
      <HeroSlider />

      <section className="section">
        <div className="section-head container">
          <h2>{t("home.shopByCategory")}</h2>
          <Link to="/products" className="text-link">{t("common.viewAll")}</Link>
        </div>
        <div className="category-grid container">
          {categories.map((c) => (
            <Link key={c.key} to={`/category/${encodeURIComponent(c.key)}`} className="category-card">
              <div className="category-card-media">
                <img src={c.image} alt={c.name} loading="lazy" />
              </div>
              <div className="category-card-info">
                <span>{c.name}</span>
                <small>{t("home.productCount", { count: c.productCount })}</small>
              </div>
            </Link>
          ))}
        </div>
      </section>

      <section className="section">
        <div className="section-head container">
          <h2>{t("home.newArrivals")}</h2>
          <Link to="/products?sort=newest" className="text-link">{t("common.viewAll")}</Link>
        </div>
        <div className="product-grid container">
          {newArrivals.map((p) => (
            <ProductCard key={p.id} product={p} />
          ))}
        </div>
      </section>

      <section className="section section-alt">
        <div className="section-head container">
          <h2>{t("home.topRated")}</h2>
          <Link to="/products?sort=popular" className="text-link">{t("common.viewAll")}</Link>
        </div>
        <div className="product-grid container">
          {popular.map((p) => (
            <ProductCard key={p.id} product={p} />
          ))}
        </div>
      </section>
    </div>
  );
}
