# Wholesale Marketplace — Project Roadmap

**Goal:** A simple, clean, slightly modern B2B retailer/wholesaler platform (inspired by centrumhurt.pl) with a seller panel for managing categories, sub-categories, and products.

**Design philosophy:** Keep scope lean. No unnecessary bells and whistles — clear catalog, easy browsing, functional seller tools, simple checkout. Modern UI (clean typography, whitespace, responsive), not a feature-bloated marketplace.

---

## Phase 0 — Foundations (Week 1) ✅ done in this repo
- [x] Finalize tech stack: FastAPI + PostgreSQL + SQLAlchemy/Alembic (backend), Next.js + Tailwind (frontend)
- [x] Set up repo structure (monorepo)
- [x] Set up local dev environment (Docker Compose: API + Postgres + Redis)
- [x] Define core DB schema v1: users, sellers, categories, products, product_variants, orders, order_items
- [x] Set up basic CI (lint + test on push)

## Phase 1 — Auth & Roles (Week 1–2)
## Phase 2 — Category System (Week 2)
## Phase 3 — Product Catalog & Seller Panel (Week 3–4)
## Phase 4 — Storefront (Week 4–5)
## Phase 5 — Orders & Notifications (Week 5–6)
## Phase 6 — Polish & Launch Prep (Week 6–7)

(See project chat history for full phase breakdowns.)

## Post-MVP / Future
- Bulk product import via CSV/Excel
- Payment gateway integration
- Advanced search (Meilisearch/Typesense) once catalog grows
- Multi-image galleries, product reviews
- Promotions/discount codes
- Multi-language support
