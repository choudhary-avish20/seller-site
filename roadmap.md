# WolkaGo — Project Roadmap

**Goal:** A simple, clean, slightly modern B2B retailer/wholesaler platform (inspired by centrumhurt.pl) with an admin/seller panel for managing categories, sub-categories, and products.

**Design philosophy:** Keep scope lean. No unnecessary bells and whistles — clear catalog, easy browsing, functional seller tools, simple checkout. Modern UI (clean typography, whitespace, responsive), not a feature-bloated marketplace.

**Actual stack (as built — supersedes any earlier planning docs):** FastAPI + SQLAlchemy/Alembic backend, SQLite by default (Postgres supported via `DATABASE_URL`, no Docker/Redis required). Plain HTML/CSS/vanilla JS frontend served directly by FastAPI — no Next.js, no build step. Payment is COD-only by design (no payment gateway is planned or needed).

**Scope decision:** this is a single-store site. "Seller" and "admin" are both staff roles managing one shared catalog, not independent vendors in a multi-tenant marketplace — there is no per-seller storefront, order splitting, or payout logic, and none is planned. Products have no owner field; any seller/admin account can manage the full catalog.

---

## Phase 0 — Foundations ✅ done
- [x] Tech stack finalized (see above)
- [x] Repo structure (backend/frontend in one repo)
- [x] Local dev environment (`./start.sh`, no Docker needed)
- [x] Core DB schema + Alembic migrations (users, sellers, categories, products, variants, price tiers, orders, order items, site settings, email verification tokens)
- [ ] CI (lint + test on push) — not set up

## Phase 1 — Auth & Roles ✅ mostly done
- [x] User model with roles: buyer, seller, admin
- [x] JWT auth (signup, login, refresh, email verification)
- [x] Seller registration flow (business info, pending approval)
- [x] Role-gated API routes (buyer vs seller/admin enforced server-side)
- [ ] Admin approval screen in the UI — the backend endpoints exist (`/sellers/pending`, `/sellers/{id}/approve`) but there's no admin-dashboard view wired to them yet

## Phase 2 — Category System ✅ mostly done
- [x] Self-referencing category tree, admin CRUD
- [x] Category tree API
- [ ] Seller "request new category" flow — schemas exist (`CategoryRequestCreate/Response/Decision`) but there's no backing model, table, or route; this is unused/dead code, not a shipped feature

## Phase 3 — Product Catalog & Seller Panel ✅ mostly done
- [x] Product model: name, description, images, category, pack size, tiered pricing, VAT, variants, stock
- [x] Admin/seller panel: product list, add/edit form, archive, stock toggle, image upload
- [x] Merchandising badges (bestseller/popular/on-sale) and sale pricing
- [ ] Per-seller product ownership — intentionally out of scope per the single-store decision above

## Phase 4 — Storefront ✅ mostly done
- [x] Homepage with category sidebar, tabs (new/popular/frequent/bestseller/sale)
- [x] Product detail page with tiered pricing, variants, recommendations
- [x] Cart (pack-quantity based) and COD checkout
- [ ] Search — the search box submits to `search.html`, which doesn't exist yet
- [ ] Pagination / price-range filtering — backend supports `page`/`limit`, frontend doesn't use them yet

## Phase 5 — Orders & Notifications ✅ mostly done
- [x] Order model with status (pending/confirmed/shipped/delivered/cancelled)
- [x] Email notifications: order confirmation, status change, product-archived notice
- [x] Stock decrement on order, restored on cancellation
- [ ] Admin order-status controls only cover delivered/cancelled in the UI — confirmed/shipped need buttons too
- [ ] Buyer-facing order history page — the API already scopes `GET /orders` to the buyer's own orders, just no page uses it yet

## Phase 6 — Polish & Launch Prep — not started
- [ ] Responsive pass on the admin dashboard (currently desktop-only)
- [ ] Static pages: FAQ, Shipping costs, Terms are still dead `#` links; Contact page is done
- [ ] Basic SEO (meta tags, sitemap)
- [ ] Production deployment (`start.sh` is dev-only: single-process `uvicorn --reload`, no process manager/HTTPS/CI)

---

## Post-MVP / Future (not in scope)
- Bulk product import via CSV/Excel
- Advanced search (Meilisearch/Typesense) once catalog grows
- Multi-image galleries, product reviews
- Promotions/discount codes beyond the current sale-price/tier system
- Multi-language support beyond the current PL/EN toggle
- Payment gateway integration — explicitly not wanted; COD-only is the intended design
