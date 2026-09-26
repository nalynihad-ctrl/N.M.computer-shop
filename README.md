# Naly,munib - E-commerce Website

A full-stack computer parts &amp; gaming accessories e-commerce website built from the
[implementation plan](implementation-plan.md).

- **Backend:** Python (Flask) REST API
- **Database:** MySQL (primary) with automatic SQLite fallback when MySQL is not running
- **Frontend:** React (Vite)

## Features

Everything in the plan's **Priority 1**, most of **Priority 2**, and the data layer:

- Responsive header with logo, search bar, cart counter and account icon
- Horizontally scrollable category menu (15+ categories)
- Auto-playing hero slider with prev/next and pagination dots
- Product cards with rating, discount badge, stock status, "Add to Cart" and "Buy Now"
- Filtering by category, brand (multi-select) and price range
- Sorting by popularity, newest, price and name
- Full-text search across name, brand, category, description and specs
- Product details page with technical specifications and related products
- Cart with quantity controls, remove, automatic totals, persisted in `localStorage`
- Buy Now flow → redirects to the cart; Checkout → creates a real order
- Simple auth (register / login / logout) with order history for logged-in users
- Dark gaming theme, fully responsive (mobile hamburger menu, adaptive grids)

## Project structure

```
computer-shop/
├── implementation-plan.md      # the plan this site implements
├── README.md
├── backend/
│   ├── app.py                  # Flask app + all API routes + SPA serving
│   ├── config.py               # DB config (env vars), shipping rules
│   ├── db.py                   # MySQL-first / SQLite-fallback database layer
│   ├── schema.sql              # MySQL schema reference (auto-created by app)
│   ├── seed_data.py            # 55 sample products across 16 categories
│   ├── requirements.txt
│   ├── static/uploads/         # product images (generated SVGs)
│   ├── tools/generate_placeholders.py
│   └── data/                   # SQLite fallback database (created on first run)
└── frontend/
    ├── src/
    │   ├── api.js
    │   ├── App.jsx             # routes + layout
    │   ├── context/            # Cart, Auth, Toast providers
    │   ├── components/         # Header, CategoryMenu, HeroSlider, ProductCard, Footer...
    │   └── pages/              # Home, Products, ProductDetails, Cart, Checkout,
    │                           # Login, Register, Profile, Orders, About, Contact
    └── dist/                   # production build (served by Flask)
```

## Running it

> The site is already built and the backend is running at **http://localhost:5000**.
> Just open it in a browser.

### From scratch

1. **Backend**

   ```bash
   cd backend
   pip install -r requirements.txt
   python app.py
   ```

   Open http://localhost:5000 — the API *and* the built React app are served from one port.
   On first start the database schema is created automatically and the 55 sample
   products are seeded.

2. **Frontend (development mode with hot reload)**

   ```bash
   cd frontend
   npm install
   npm run dev      # http://localhost:5173  (proxies /api and /uploads to :5000)
   ```

   In production you only need the backend; the compiled app lives in `frontend/dist`
   and is served at `/`. Rebuild after frontend changes with `npm run build`.

## Database: MySQL with SQLite fallback

The app always tries **MySQL first**. On startup it prints which backend it chose:

- It connects to MySQL and automatically creates the `computer_shop` database, all
  tables and the seed data.
- If MySQL isn't reachable (not installed, wrong password, or `PyMySQL` missing) it
  transparently falls back to a local SQLite file at `backend/data/computer_shop.db`,
  so the whole site still works and you can switch to MySQL later with no code changes.

Configure MySQL via environment variables (defaults shown):

```
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DB=computer_shop
```

## API overview

| Method | Route                  | Description                                   |
| ------ | ---------------------- | --------------------------------------------- |
| GET    | `/api/health`          | Server + chosen database                      |
| GET    | `/api/categories`      | Category list with counts and image           |
| GET    | `/api/brands`          | Distinct brand list                           |
| GET    | `/api/products`        | Products: `?category&brand&search&sort&minPrice&maxPrice&limit` |
| GET    | `/api/products/:id`    | Single product with specs and images          |
| POST   | `/api/auth/register`   | Create account → `{ token, user }`            |
| POST   | `/api/auth/login`      | Login → `{ token, user }`                     |
| GET    | `/api/auth/me`         | Current user (Bearer token)                   |
| POST   | `/api/auth/logout`     | Invalidate token                              |
| POST   | `/api/checkout`        | Create order from `{ items, ...customer }`    |
| GET    | `/api/orders`          | Order history for the logged-in user          |

Checkout removes ordered quantities from stock and returns the new order id.

## Product images

Free-to-use hardware images could not be reliably downloaded from image CDNs during
setup, so the store ships with **locally generated SVG product images** (one per
category). They are created by `backend/tools/generate_placeholders.py` and stored in
`backend/static/uploads/`. To use real photos later, just save JPEG/PNG files into
`static/uploads/` and update the `image` value in `backend/seed_data.py` (or via the
`products.image` column).

## Roadmap (from the plan)

Priority 3 items that remain future work:

- Real database integration switch (MySQL already supported, see above)
- Admin dashboard with product &amp; inventory management
- Real payment gateway behind the current "Cash on Delivery" / "Card Payment" step
- Order management / status updates
- Order confirmation emails and address book