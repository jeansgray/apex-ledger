#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
export PATH="$HOME/.local/bin:${PATH:-}"

PY312="$(uv python find 3.12)"

if ! curl -sf http://127.0.0.1:5001/health >/dev/null 2>&1; then
  nohup env UV_PYTHON="$PY312" uv run --directory vendor/mirofish/backend python run.py \
    > /tmp/mirofish.log 2>&1 &
  echo "Starting MiroFish on :5001 (log: /tmp/mirofish.log)"
fi

if ! curl -sf http://127.0.0.1:8080/health >/dev/null 2>&1; then
  nohup uv run uvicorn apex_ledger.api.app:app --host 0.0.0.0 --port 8080 \
    > /tmp/apex-ledger.log 2>&1 &
  echo "Starting Apex Ledger on :8080 (log: /tmp/apex-ledger.log)"
fi
