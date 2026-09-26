import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import HeroSlider from "../components/HeroSlider";
import ProductCard from "../components/ProductCard";
import { api } from "../api";

export default function Home() {
  const [categories, setCategories] = useState([]);
  const [newArrivals, setNewArrivals] = useState([]);
  const [popular, setPopular] = useState([]);

  useEffect(() => {
    api.getCategories().then(setCategories).catch(() => {});
    api.getProducts({ sort: "newest", limit: 8 }).then(setNewArrivals).catch(() => {});
    api.getProducts({ sort: "popular", limit: 8 }).then(setPopular).catch(() => {});
  }, []);

  return (
    <div className="home">
      <HeroSlider />

      <section className="section">
        <div className="section-head container">
          <h2>Shop by Category</h2>
          <Link to="/products" className="text-link">View all →</Link>
        </div>
        <div className="category-grid container">
          {categories.map((c) => (
            <Link key={c.name} to={`/category/${encodeURIComponent(c.name)}`} className="category-card">
              <div className="category-card-media">
                <img src={c.image} alt={c.name} loading="lazy" />
              </div>
              <div className="category-card-info">
                <span>{c.name}</span>
                <small>{c.productCount} products</small>
              </div>
            </Link>
          ))}
        </div>
      </section>

      <section className="section">
        <div className="section-head container">
          <h2>New Arrivals</h2>
          <Link to="/products?sort=newest" className="text-link">View all →</Link>
        </div>
        <div className="product-grid container">
          {newArrivals.map((p) => (
            <ProductCard key={p.id} product={p} />
          ))}
        </div>
      </section>

      <section className="section section-alt">
        <div className="section-head container">
          <h2>Top Rated</h2>
          <Link to="/products?sort=popular" className="text-link">View all →</Link>
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