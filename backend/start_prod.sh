#!/usr/bin/env bash
# start_prod.sh — production startup script for Render
# Runs DB migrations then starts the uvicorn server.
set -e

echo "→ Running Alembic migrations"
alembic upgrade head

echo "→ Starting uvicorn"
# Render sets PORT automatically; fall back to 8000 for local testing
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --workers 1 \
  --log-level info
