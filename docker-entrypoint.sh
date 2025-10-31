#!/bin/sh
set -e

echo "[entrypoint] Waiting for database..."
python manage.py migrate --noinput || { echo "Migrations failed"; exit 1; }

echo "[entrypoint] Seeding roles..."
python manage.py seed_roles || echo "seed_roles failed (non-fatal)"

echo "[entrypoint] Seeding admin (will retry if DB temporarily unavailable)..."
python manage.py seed_admin || echo "seed_admin failed (non-fatal)"

echo "[entrypoint] Starting server..."
exec python manage.py runserver 0.0.0.0:8000
