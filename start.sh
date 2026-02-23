#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PORT="${PORT:-8080}"
echo "Starting server on 0.0.0.0:${PORT}"
exec python3 -m uvicorn server:app --host 0.0.0.0 --port "$PORT"
