#!/usr/bin/env zsh
# start.sh — run the seller site locally (no Docker needed)
set -e

SCRIPT_DIR="${0:A:h}"
BACKEND="$SCRIPT_DIR/backend"

# ── 1. Create .env if it doesn't exist ────────────────────────────────────
if [[ ! -f "$BACKEND/.env" ]]; then
  echo "→ Creating backend/.env from .env.example"
  cp "$BACKEND/.env.example" "$BACKEND/.env"
fi

# ── 2. Create / activate virtualenv ───────────────────────────────────────
if [[ ! -d "$BACKEND/venv" ]]; then
  echo "→ Creating Python virtualenv"
  python3 -m venv "$BACKEND/venv"
fi

source "$BACKEND/venv/bin/activate"

# ── 3. Install dependencies ────────────────────────────────────────────────
echo "→ Installing Python dependencies"
pip install -q -r "$BACKEND/requirements.txt"

# ── 4. Run DB migrations ───────────────────────────────────────────────────
echo "→ Running Alembic migrations"
cd "$BACKEND"
alembic upgrade head

# ── 5. Seed admin / seller account (only if DB is empty) ──────────────────
if python3 - <<'EOF'
import sqlite3, os, sys
db = os.path.join(os.path.dirname(os.path.abspath(".")), "backend", "wholesale.db")
# quick check — if users table has any row, skip seeding
try:
    conn = sqlite3.connect("wholesale.db")
    count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    sys.exit(0 if count == 0 else 1)
except Exception:
    sys.exit(0)
EOF
then
  echo "→ Seeding seller account (email: seller@example.com  password: seller123)"
  python3 seed_admin.py
fi

# ── 6. Start server ────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  Site:      http://localhost:8000                ║"
echo "║  Dashboard: http://localhost:8000/admin-dashboard.html ║"
echo "║  API docs:  http://localhost:8000/docs           ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

cd "$BACKEND"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
