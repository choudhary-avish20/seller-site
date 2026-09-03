#!/usr/bin/env bash
# start_prod.sh — production startup script for Render
# Runs DB migrations then starts the uvicorn server.
set -e

echo "→ Running Alembic migrations"
alembic upgrade head

echo "→ Ensuring admin account exists"
# Safe to run on every boot: seed_admin() no-ops if ADMIN_EMAIL already exists,
# it never duplicates the account or touches an existing password.
python seed_admin.py

echo "→ Starting uvicorn"
# Render sets PORT automatically; fall back to 8000 for local testing
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --workers 1 \
  --log-level info
