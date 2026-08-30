# Seller Site

A single-owner storefront: the seller manages products, categories, and orders
through a private dashboard; customers browse the catalogue and place orders.

## Stack

- **Backend:** FastAPI · SQLAlchemy 2 · Alembic · SQLite (default) / PostgreSQL
- **Frontend:** Plain HTML/CSS/JS — no build step, served directly by FastAPI

---

## Quick start (no Docker required)

### Prerequisites

- Python 3.11+

That's it. SQLite is used by default so no database server is needed.

### 1 — Clone & enter the repo

```bash
git clone <repo-url>
cd seller-site
```

### 2 — One-command start

```bash
./start.sh
```

`start.sh` will:
1. Copy `backend/.env.example` → `backend/.env` (first run only)
2. Create a Python virtualenv inside `backend/venv/`
3. Install dependencies from `requirements.txt`
4. Run Alembic migrations (creates `backend/wholesale.db`)
5. Seed a seller account if the DB is empty
6. Start the dev server on **http://localhost:8000**

### 3 — Open the site

| URL | What you get |
|-----|-------------|
| http://localhost:8000 | Customer storefront |
| http://localhost:8000/admin-dashboard.html | Seller dashboard |
| http://localhost:8000/docs | Interactive API docs |

### Default seller credentials (seeded on first run)

| Field | Value |
|-------|-------|
| Email | `seller@example.com` |
| Password | `seller123` |

Change these after first login by editing `backend/seed_admin.py` before the
first run, or directly in the database.

---

## Manual setup (step by step)

```bash
cd backend

# copy env
cp .env.example .env          # edit SECRET_KEY for production

# virtualenv
python3 -m venv venv
source venv/bin/activate

# dependencies
pip install -r requirements.txt

# migrate
alembic upgrade head

# seed seller account
python3 seed_admin.py

# run
uvicorn app.main:app --reload --port 8000
```

---

## Switching to PostgreSQL

Edit `backend/.env`:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/sellersite
```

Then re-run migrations:

```bash
cd backend
source venv/bin/activate
alembic upgrade head
```

---

## Creating a new migration

After changing a model in `backend/app/models/`:

```bash
cd backend
source venv/bin/activate
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

---

## Project structure

```
seller-site/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # FastAPI routers (auth, products, categories, orders, …)
│   │   ├── core/            # config, JWT auth helpers
│   │   ├── db/              # SQLAlchemy engine + session
│   │   ├── models/          # ORM models
│   │   └── schemas/         # Pydantic request/response models
│   ├── alembic/             # DB migrations
│   ├── requirements.txt
│   └── seed_admin.py        # seeds the seller account
├── frontend/
│   ├── index.html           # customer storefront
│   ├── product.html         # product detail page
│   ├── cart.html            # shopping cart
│   ├── login.html           # login
│   ├── signup.html          # buyer registration
│   ├── register-seller.html # seller registration
│   ├── admin-dashboard.html # seller dashboard (products / categories / orders)
│   ├── js/app.js            # shared API client, cart, auth helpers
│   └── css/style.css
└── start.sh                 # one-command local dev starter
```

## Seller dashboard features

- **Products** — add, edit, archive/restore, delete; image uploads; tiered pricing; stock management
- **Categories** — view the full category tree (add/edit via API or dashboard)
- **Orders** — see all customer orders with buyer details; print order view for fulfilment
