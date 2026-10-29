#!/usr/bin/env bash
# Reset the lab target to a clean, freshly-seeded state.
#
# Drops the target database volume and recreates the target services, so the
# seed SQL in lab/target/seed/ runs again. Run between engagements / after any
# test that mutated target data.
set -euo pipefail

cd "$(dirname "$0")/.."   # -> lab/

echo "[redkeep] Stopping target services and removing the DB volume..."
docker compose stop target-db target-api target-platform target-admin target-reports target-ui
docker compose rm -f target-db
docker volume rm -f redkeep-lab_target-db-data || true

echo "[redkeep] Recreating target (DB will re-run seed SQL)..."
docker compose up -d target-db
# Give Postgres a moment to initialise + seed before the apps connect.
sleep 5
docker compose up -d target-api target-platform target-admin target-reports target-ui

echo "[redkeep] Lab target reset complete."
