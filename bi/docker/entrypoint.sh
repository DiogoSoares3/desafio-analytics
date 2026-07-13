#!/usr/bin/env bash
# One-shot bootstrap for the local Superset container: migrate the metadata DB, create the
# admin user, initialize roles/permissions, import the committed bi/ bundle (ADR-0002), then
# start the web server. Idempotent — safe to re-run on every container start.
set -euo pipefail

superset db upgrade

superset fab create-admin \
    --username "${SUPERSET_ADMIN_USERNAME:-admin}" \
    --firstname Admin \
    --lastname Admin \
    --email "${SUPERSET_ADMIN_EMAIL:-admin@example.com}" \
    --password "${SUPERSET_ADMIN_PASSWORD:-admin}" \
    || true

superset init

superset import-directory /app/bi --overwrite

exec gunicorn \
    --bind "0.0.0.0:8088" \
    --workers 2 \
    --timeout 120 \
    "superset.app:create_app()"
