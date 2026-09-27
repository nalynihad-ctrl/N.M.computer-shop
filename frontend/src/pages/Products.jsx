import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import ProductCard from "../components/ProductCard";
import { api } from "../api";
import { useLanguage } from "../context/LanguageContext";

export default function Products({ categoryMode }) {
  const { language, t } = useLanguage();
  const { category: paramCategory } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();

  const [products, setProducts] = useState([]);
  const [brands, setBrands] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // The category in the URL is always the canonical English key, so it is
  // stable across languages and can be handed straight to the API filter. Only
  // its display name needs translating, which the category list below provides.
  const activeCategory = categoryMode ? paramCategory : searchParams.get("category") || "";
  const search = searchParams.get("search") || "";
  const sort = searchParams.get("sort") || "popular";
  const priceMin = searchParams.get("minPrice") || "";
  const priceMax = searchParams.get("maxPrice") || "";
  const selectedBrands = (searchParams.get("brand") || "").split(",").filter(Boolean);
  const brandKey = selectedBrands.join(",");

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

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    const params = {
      category: activeCategory || undefined,
      search: search || undefined,
      sort,
      minPrice: priceMin || undefined,
      maxPrice: priceMax || undefined,
      brand: brandKey || undefined,
    };
    try {
      const data = await api.getProducts(params);
      setProducts(data);
      setBrands(await api.getBrands());
    } catch (e) {
      setError(e.message || "Failed to load products.");
    } finally {
      setLoading(false);
    }
    // `language` is a dependency because the product names, descriptions and
    // spec labels come from the server in the active language: without it, a
    // language switch would leave the previous language's text on screen.
  }, [activeCategory, search, sort, priceMin, priceMax, brandKey, language]);

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [load]);

  const update = (patch) => {
    const next = new URLSearchParams(searchParams);
    for (const [k, v] of Object.entries(patch)) {
      if (v === undefined || v === null || v === "" || v === false) next.delete(k);
      else next.set(k, v);
    }
    setSearchParams(next, { replace: true });
  };

  const toggleBrand = (name) => {
    const next = selectedBrands.includes(name)
      ? selectedBrands.filter((b) => b !== name)
      : [...selectedBrands, name];
    update({ brand: next.join(",") });
  };

  // Display name for the key in the URL. Falls back to the key itself, which
  // only happens for a category the API no longer knows about.
  const categoryName = useMemo(() => {
    const found = categories.find((c) => c.key === activeCategory);
    return found ? found.name : activeCategory;
  }, [categories, activeCategory]);

  const title = activeCategory
    ? t("products.titleCategory", { category: categoryName })
    : search
    ? t("products.titleSearch", { search })
    : t("products.titleAll");

  return (
    <div className="products-page container">
      <nav className="breadcrumb">
        <Link to="/">{t("nav.home")}</Link>
        {activeCategory ? (
          <>
            {" / "}
            <Link to="/products">{t("nav.allProducts")}</Link>
            <span> / {categoryName}</span>
          </>
        ) : (
          <>
            {" / "}
            <span>{t("nav.allProducts")}</span>
          </>
        )}
      </nav>

      <h1 className="page-title">{title}</h1>

      <div className="products-layout">
        <aside className="filters">
          <div className="filter-group">
            <h3>{t("filters.category")}</h3>
            <Link to="/products" className={!activeCategory ? "active" : ""}>
              {t("filters.allProducts")}
            </Link>
            {!categoryMode && (
              <select
                value={activeCategory}
                onChange={(e) => update({ category: e.target.value })}
                className="input"
                aria-label={t("filters.category")}
              >
                <option value="">{t("filters.allCategories")}</option>
                {categories.map((c) => (
                  <option key={c.key} value={c.key}>
                    {c.name}
                  </option>
                ))}
              </select>
            )}
          </div>

          <div className="filter-group">
            <h3>{t("filters.brand")}</h3>
            {brands.map((b) => (
              <label key={b} className="checkbox">
                <input
                  type="checkbox"
                  checked={selectedBrands.includes(b)}
                  onChange={() => toggleBrand(b)}
                />
                {b}
              </label>
            ))}
          </div>

          <div className="filter-group">
            <h3>{t("filters.price")}</h3>
            <div className="price-range">
              <input
                type="number"
                placeholder={t("filters.min")}
                aria-label={t("filters.min")}
                className="input"
                value={priceMin}
                onChange={(e) => update({ minPrice: e.target.value })}
              />
              <span>{t("filters.to")}</span>
              <input
                type="number"
                placeholder={t("filters.max")}
                aria-label={t("filters.max")}
                className="input"
                value={priceMax}
                onChange={(e) => update({ maxPrice: e.target.value })}
              />
            </div>
            <button
              className="btn btn-ghost btn-sm"
              onClick={() => update({ minPrice: "", maxPrice: "" })}
            >
              {t("filters.clearPrices")}
            </button>
          </div>
        </aside>

        <div className="products-main">
          <div className="toolbar">
            {search ? (
              <button
                className="btn btn-ghost btn-sm"
                onClick={() => setSearchParams({ sort: sort || "" }, { replace: true })}
              >
                {t("toolbar.clearSearch")}
              </button>
            ) : (
              <span className="toolbar-count">
                {t("toolbar.productCount", { count: products.length })}
              </span>
            )}
            <select
              className="input sort-select"
              value={sort}
              aria-label={t("sort.label")}
              onChange={(e) => update({ sort: e.target.value })}
            >
              <option value="popular">
                {t("sort.label")}: {t("sort.popular")}
              </option>
              <option value="newest">
                {t("sort.label")}: {t("sort.newest")}
              </option>
              <option value="price_asc">
                {t("sort.label")}: {t("sort.priceAsc")}
              </option>
              <option value="price_desc">
                {t("sort.label")}: {t("sort.priceDesc")}
              </option>
              <option value="name">
                {t("sort.label")}: {t("sort.name")}
              </option>
            </select>
          </div>

          {error && <div className="notice">{t("products.loadError")}</div>}

          {!error && loading && (
            <div className="product-grid">
              {Array.from({ length: 8 }, (_, i) => (
                <div key={i} className="skeleton-card" />
              ))}
            </div>
          )}

          {!error && !loading && products.length === 0 && (
            <div className="empty-state">
              <p>{t("products.empty")}</p>
              <p className="muted">{t("products.emptyHint")}</p>
              <Link to="/products" className="btn btn-primary">
                {t("products.viewAll")}
              </Link>
            </div>
          )}

          {!error && !loading && products.length > 0 && (
            <div className="product-grid">
              {products.map((p) => (
                <ProductCard key={p.id} product={p} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
