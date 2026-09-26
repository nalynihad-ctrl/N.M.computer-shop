import { useEffect, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { api } from "../api";

export default function CategoryMenu() {
  const [categories, setCategories] = useState([]);
  const trackRef = useRef(null);
  const location = useLocation();

  const match = location.pathname.match(/^\/category\/([^/]+)/);
  const activeCategory = match ? decodeURIComponent(match[1]) : null;

  useEffect(() => {
    let alive = true;
    api
      .getCategories()
      .then((data) => {
        if (alive) setCategories(data);
      })
      .catch(() => {});
    return () => {
      alive = false;
    };
  }, []);

  const isActive = (name) => name === activeCategory;

  const scroll = (dir) => {
    const track = trackRef.current;
    if (!track) return;
    track.scrollBy({ left: dir * 200, behavior: "smooth" });
  };

  return (
    <div className="category-menu">
      <div className="category-bar container">
        <button
          type="button"
          className="category-arrow category-arrow-left"
          aria-label="Scroll categories left"
          onClick={() => scroll(-1)}
        >
          &#8249;
        </button>
        <div className="category-track" ref={trackRef}>
          <Link
            to="/products"
            className={`category-item ${!activeCategory ? "active" : ""}`}
          >
            All Products
          </Link>
          {categories.map((c) => (
            <Link
              key={c.name}
              to={`/category/${encodeURIComponent(c.name)}`}
              className={`category-item ${isActive(c.name) ? "active" : ""}`}
            >
              <img src={c.image} alt="" width="22" height="22" loading="lazy" />
              <span>{c.name}</span>
            </Link>
          ))}
        </div>
        <button
          type="button"
          className="category-arrow category-arrow-right"
          aria-label="Scroll categories right"
          onClick={() => scroll(1)}
        >
          &#8250;
        </button>
      </div>
    </div>
  );
}
