#!/usr/bin/env bash
# Launch the Redkeep UI (local control panel) and open it in the browser.
# Stops when you close this window — nothing is left running.
set -euo pipefail
cd "$(dirname "$0")"
PY="$(command -v python3 || command -v python || true)"
if [ -z "$PY" ]; then
  echo "Python 3 is required but was not found on PATH." >&2
  exit 1
fi
exec "$PY" ui/server.py "$@"
