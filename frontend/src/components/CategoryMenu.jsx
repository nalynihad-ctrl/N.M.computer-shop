import { useEffect, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { api } from "../api";
import { useLanguage } from "../context/LanguageContext";

export default function CategoryMenu() {
  const { language, t } = useLanguage();
  const [categories, setCategories] = useState([]);
  const trackRef = useRef(null);
  const location = useLocation();

  // The URL segment is the canonical English category key, never the translated
  // name, so a shared /category/GPUs link means the same thing in every language
  // and the API can filter on it without reverse-mapping a translation.
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
  }, [language]);

  const isActive = (key) => key === activeCategory;

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
          aria-label={t("a11y.scrollCategoriesLeft")}
          onClick={() => scroll(-1)}
        >
          &#8249;
        </button>
        <div className="category-track" ref={trackRef}>
          <Link
            to="/products"
            className={`category-item ${!activeCategory ? "active" : ""}`}
          >
            {t("nav.allProducts")}
          </Link>
          {categories.map((c) => (
            <Link
              key={c.key}
              to={`/category/${encodeURIComponent(c.key)}`}
              className={`category-item ${isActive(c.key) ? "active" : ""}`}
            >
              <img src={c.image} alt="" width="22" height="22" loading="lazy" />
              <span>{c.name}</span>
            </Link>
          ))}
        </div>
        <button
          type="button"
          className="category-arrow category-arrow-right"
          aria-label={t("a11y.scrollCategoriesRight")}
          onClick={() => scroll(1)}
        >
          &#8250;
        </button>
      </div>
    </div>
  );
}
