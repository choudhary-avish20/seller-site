# Vanilla Frontend — No Frameworks

Fast, no-build, pure HTML/CSS/JS storefront for Wholesale Marketplace. Solves slow Next.js rendering by removing React/TS build and hydration.

## Run

**Via backend (recommended):**
```bash
cd backend && uvicorn app.main:app --port 8000 --reload
# open http://localhost:8000/vanilla/
```

**Standalone (no backend build):**
```bash
cd vanilla
python -m http.server 3001
# open http://localhost:3001/
# set API_URL if backend not on localhost:8000:
# localStorage.setItem('API_URL','http://localhost:8000/api/v1')
```

## Structure
```
vanilla/
  index.html              # homepage (hero, featured, new arrivals)
  css/style.css           # modern CentrumHurt-inspired, vanilla, responsive
  js/
    api.js                # fetch wrapper, token refresh, getImageUrl()
    auth.js               # login/signup, token storage
    cart.js               # pack-quantity cart in localStorage
    i18n.js               # PL/EN toggle, DICT, t()
    common.js             # header/footer injection
  login.html, signup.html, register-seller.html
  categories.html, category.html?slug=, product.html?slug=, search.html?q=
  cart.html, checkout.html, checkout-success.html?orderId=
  seller.html, seller-products.html, seller-product-new.html
  admin.html, buyer-orders.html
```

## Pages (all vanilla)
- Storefront: `index.html`, `categories.html`, `category.html`, `product.html`, `search.html`
- Cart: `cart.html` (pack qty), `checkout.html` → `checkout-success.html` (COD, POST /orders)
- Auth: `login.html`, `signup.html`, `register-seller.html`
- Seller: `seller.html` (status), `seller-products.html` (list, toggle stock, archive, delete), `seller-product-new.html` (create with upload)
- Admin: `admin.html` (approve sellers & category requests)

## Images
- Real uploads: `POST /api/v1/uploads/image` → `backend/uploads/products/` → `http://localhost:8000/uploads/products/{file}`
- Test images: drop .jpg/.png into `assets/test-images/` → `GET /api/v1/uploads/test-images` → pick in seller form

## Language Toggle
Top bar `PL | EN` pill — `js/i18n.js` `setLang()`, persisted `localStorage.lang`, updates `[data-i18n]` attributes. No reload needed for header, homepage reloads for full page.

## Why faster
- No Next.js hydration, no TS compilation, no 87kB shared JS — just 5 small vanilla files (<12kB total)
- Instant first paint, <50ms TTFB vs Next.js dev 800ms+ pre-render
- Same FastAPI backend, same modern UI, but zero framework overhead

## Next.js legacy
Original `frontend/` (Next.js/TS) kept for reference. To fully revamp, replace `frontend/` with `vanilla/` or keep both: Next.js at :3000, vanilla at :8000/vanilla or :3001.

