# Wholesale Marketplace

A lean, modern B2B retailer/wholesaler platform. FastAPI + PostgreSQL backend,
Next.js + Tailwind frontend.

## Stack

- **Backend:** FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL, Redis (optional, for later phases)
- **Frontend:** Next.js 14 (App Router), Tailwind CSS, TypeScript
- **Infra:** Docker Compose for local dev

## Project structure

```
wholesale-marketplace/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # FastAPI routers
│   │   ├── core/            # config, security
│   │   ├── db/              # engine/session, declarative base
│   │   ├── models/          # SQLAlchemy ORM models (schema v1)
│   │   └── schemas/         # Pydantic request/response schemas
│   ├── alembic/              # DB migrations
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   └── src/app/               # Next.js App Router pages
├── docker-compose.yml
└── .github/workflows/ci.yml
```

## Schema v1

- `users` — buyer / seller / admin roles
- `seller_profiles` — 1:1 with users where role=seller; approval workflow (pending/approved/rejected)
- `categories` — self-referencing tree (`parent_id`)
- `products` — belongs to a seller + category; wholesale pack pricing (net/gross, `pack_size`)
- `product_variants` — size/color options per product, optional price/stock override
- `orders` — belongs to a buyer; status lifecycle (pending → confirmed → shipped → delivered / cancelled)
- `order_items` — line items with price/name snapshots so historical orders don't change if a product is edited later

## Local development

1. Copy the backend env file:
   ```bash
   cp backend/.env.example backend/.env
   ```
2. Start everything:
   ```bash
   docker compose up --build
   ```
3. Services:
   - API: http://localhost:8000 (docs at `/docs`)
   - Frontend: http://localhost:3000
   - Postgres: localhost:5432 (`wholesale` / `wholesale`)

The `api` container runs `alembic upgrade head` automatically on startup, so the
schema is migrated before Uvicorn starts.

## Creating a new migration

After changing a model in `backend/app/models/`:

```bash
docker compose exec api alembic revision --autogenerate -m "describe change"
docker compose exec api alembic upgrade head
```

## Running tests / lint

```bash
# backend
docker compose exec api pytest -q
docker compose exec api ruff check .

# frontend
docker compose exec web npm run lint
```

## Roadmap

See `PROJECT_ROADMAP.md` for the full phase-by-phase plan. This repo currently
implements **Phase 0**: foundations — empty but running API connected to
Postgres, migrated schema v1, and a connected Next.js shell.
