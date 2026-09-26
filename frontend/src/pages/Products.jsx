import { useCallback, useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import ProductCard from "../components/ProductCard";
import { api } from "../api";

export default function Products({ categoryMode }) {
  const { category: paramCategory } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();

  const [products, setProducts] = useState([]);
  const [brands, setBrands] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const activeCategory = categoryMode ? paramCategory : searchParams.get("category") || "";
  const search = searchParams.get("search") || "";
  const sort = searchParams.get("sort") || "popular";
  const priceMin = searchParams.get("minPrice") || "";
  const priceMax = searchParams.get("maxPrice") || "";
  const selectedBrands = (searchParams.get("brand") || "").split(",").filter(Boolean);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    const params = {
      category: activeCategory || undefined,
      search: search || undefined,
      sort,
      minPrice: priceMin || undefined,
      maxPrice: priceMax || undefined,
      brand: selectedBrands.length ? selectedBrands.join(",") : undefined,
    };
    try {
      const data = await api.getProducts(params);
      setProducts(data);
      const b = await api.getBrands();
      setBrands(
        activeCategory ? b : b
      );
      if (!activeCategory && !search && data.length === 0) {
        setProducts([]);
      }
    } catch (e) {
      setError(e.message || "Failed to load products.");
    } finally {
      setLoading(false);
    }
  }, [activeCategory, search, sort, priceMin, priceMax, selectedBrands.join(",")]);

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

  const title = activeCategory
    ? `Category: ${activeCategory}`
    : search
    ? `Search results for "${search}"`
    : "All Products";

  return (
    <div className="products-page container">
      <nav className="breadcrumb">
        <Link to="/">Home</Link> / {activeCategory ? <Link to="/products">Products</Link> : <span>Products</span>}
        {activeCategory && <span> / {activeCategory}</span>}
      </nav>

      <h1 className="page-title">{title}</h1>

      <div className="products-layout">
        <aside className="filters">
          <div className="filter-group">
            <h3>Category</h3>
            <Link to="/products" className={!activeCategory ? "active" : ""}>All Products</Link>
            {!categoryMode && (
              <select
                value={activeCategory}
                onChange={(e) => update({ category: e.target.value })}
                className="input"
              >
                <option value="">All categories</option>
                <CatOptions />
              </select>
            )}
          </div>

          <div className="filter-group">
            <h3>Brand</h3>
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
            <h3>Price</h3>
            <div className="price-range">
              <input
                type="number"
                placeholder="Min"
                className="input"
                value={priceMin}
                onChange={(e) => update({ minPrice: e.target.value })}
              />
              <span>to</span>
              <input
                type="number"
                placeholder="Max"
                className="input"
                value={priceMax}
                onChange={(e) => update({ maxPrice: e.target.value })}
              />
            </div>
            <button className="btn btn-ghost btn-sm" onClick={() => update({ minPrice: "", maxPrice: "" })}>
              Clear prices
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
                Clear search
              </button>
            ) : (
              <span className="toolbar-count">{products.length} products</span>
            )}
            <select
              className="input sort-select"
              value={sort}
              onChange={(e) => update({ sort: e.target.value })}
            >
              <option value="popular">Sort: Most Popular</option>
              <option value="newest">Sort: Newest</option>
              <option value="price_asc">Sort: Price (Low → High)</option>
              <option value="price_desc">Sort: Price (High → Low)</option>
              <option value="name">Sort: Name A-Z</option>
            </select>
          </div>

          {error && <div className="notice">Something went wrong while loading products.</div>}

          {!error && loading && (
            <div className="product-grid">
              {Array.from({ length: 8 }, (_, i) => (
                <div key={i} className="skeleton-card" />
              ))}
            </div>
          )}

          {!error && !loading && products.length === 0 && (
            <div className="empty-state">
              <p>No products found.</p>
              <p className="muted">Try searching for another product or clearing the filters.</p>
              <Link to="/products" className="btn btn-primary">View all products</Link>
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

function CatOptions() {
  const [categories, setCategories] = useState([]);
  useEffect(() => {
    api.getCategories().then((c) => setCategories(c.map((x) => x.name))).catch(() => {});
  }, []);
  return (
    <>
      {categories.map((c) => (
        <option key={c} value={c}>{c}</option>
      ))}
    </>
  );
}