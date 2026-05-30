#!/bin/sh
set -e

mkdir -p /app/data/mirofish_insights

FIXTURE="/app/data/mirofish_insights/sim_apex_personal_investor.json"
if [ ! -f "$FIXTURE" ]; then
  echo "Seeding demo insights fixture…"
  APEX_INSIGHTS_DIR=/app/data/mirofish_insights \
    python3 /app/scripts/seed_personal_investor_simulation.py --skip-uploads
fi

exec uv run uvicorn apex_ledger.api.app:app --host 0.0.0.0 --port 8080
