# Wholesale Marketplace — Project Roadmap

**Goal:** A simple, clean, slightly modern B2B retailer/wholesaler platform (inspired by centrumhurt.pl) with a seller panel for managing categories, sub-categories, and products.

**Design philosophy:** Keep scope lean. No unnecessary bells and whistles — clear catalog, easy browsing, functional seller tools, simple checkout. Modern UI (clean typography, whitespace, responsive), not a feature-bloated marketplace.

---

## Phase 0 — Foundations (Week 1)

- [ ] Finalize tech stack: FastAPI + PostgreSQL + SQLAlchemy/Alembic (backend), Next.js + Tailwind (frontend)
- [ ] Set up repo structure (monorepo or separate backend/frontend repos)
- [ ] Set up local dev environment (Docker Compose: API + Postgres + optional Redis)
- [ ] Define core DB schema v1: users, sellers, categories, products, product_variants, orders, order_items
- [ ] Set up basic CI (lint + test on push)

**Deliverable:** Empty but running FastAPI app + Postgres, connected Next.js shell, schema migrated.

---

## Phase 1 — Auth & Roles (Week 1–2)

- [ ] User model with roles: `buyer`, `seller`, `admin`
- [ ] JWT-based auth (signup, login, refresh token)
- [ ] Seller registration flow (business info, pending approval by admin)
- [ ] Basic admin approval screen (approve/reject sellers)
- [ ] Role-gated routing on frontend (buyer view vs seller panel vs admin)

**Deliverable:** Users can sign up as buyer or seller; sellers need admin approval before listing products.

---

## Phase 2 — Category System (Week 2)

- [ ] Category model (self-referencing `parent_id`, supports nesting)
- [ ] Admin CRUD for top-level categories (keep taxonomy centrally controlled — sellers pick from existing tree)
- [ ] Seller-facing "request new category/subcategory" flow → admin approves → added to tree
- [ ] Category tree API (fetch full tree, fetch by path/slug)

**Deliverable:** Admin can manage a nested category tree; sellers can request additions.

---

## Phase 3 — Product Catalog & Seller Panel (Week 3–4)

- [ ] Product model: name, description, images, category, seller, pack_size, price (net/gross), stock
- [ ] Product variants (size/color) as a linked table
- [ ] Seller panel UI:
  - [ ] Product list (own products only)
  - [ ] Add/edit product form (pick category → subcategory, set pack size & price, upload images)
  - [ ] Delete/archive product
  - [ ] Simple stock toggle (in stock / out of stock)
- [ ] Image upload (S3-compatible storage or local disk for MVP)

**Deliverable:** A seller can log in, request/pick a category, and list a product with pack pricing and images.

---

## Phase 4 — Storefront (Week 4–5)

- [ ] Homepage: featured/new categories, new arrivals
- [ ] Category browsing page (with subcategory sidebar, like the reference site)
- [ ] Product listing grid (pack size + net/gross price shown clearly)
- [ ] Product detail page
- [ ] Simple search (by name/category, Postgres full-text to start)
- [ ] Cart (pack-quantity based, not single units)
- [ ] Checkout flow (basic — no payment gateway yet, or COD/manual invoice to start)

**Deliverable:** A buyer can browse categories, search, add packs to cart, and place an order.

---

## Phase 5 — Orders & Notifications (Week 5–6)

- [ ] Order model: buyer, seller(s), line items, status (pending/confirmed/shipped/delivered/cancelled)
- [ ] Seller order dashboard (view incoming orders, update status)
- [ ] Buyer order history page
- [ ] Email notifications on order placed/status change (basic transactional email)

**Deliverable:** Full order lifecycle from cart → placed → seller fulfills → buyer sees status.

---

## Phase 6 — Polish & Launch Prep (Week 6–7)

- [ ] Responsive design pass (mobile-friendly storefront + seller panel)
- [ ] Basic analytics for sellers (views, orders, revenue — simple counts, no fancy charts)
- [ ] Static pages (About, Shipping/Terms, FAQ, Contact)
- [ ] Error handling, form validation, loading states across app
- [ ] Basic SEO (meta tags, sitemap, clean URLs)
- [ ] Deploy (backend + DB + frontend)

**Deliverable:** MVP ready for real sellers/buyers to use.

---

## Post-MVP / Future (not in initial scope)

- Bulk product import via CSV/Excel
- Payment gateway integration
- Advanced search (Meilisearch/Typesense) once catalog grows
- Multi-image galleries, product reviews
- Promotions/discount codes
- Multi-language support

---

## Immediate Next Step

Start **Phase 0**: scaffold the FastAPI backend + Postgres schema, and the Next.js frontend shell. We can begin with the DB schema (tables/columns in detail) and the FastAPI project structure.
