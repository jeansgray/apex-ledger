#!/bin/sh
set -e

if [ -z "${LLM_API_KEY}" ]; then
  export LLM_API_KEY=demo-placeholder
fi
if [ -z "${ZEP_API_KEY}" ]; then
  export ZEP_API_KEY=demo-placeholder
fi

FIXTURE="/app/uploads/simulations/sim_apex_personal_investor/state.json"
if [ ! -f "$FIXTURE" ]; then
  echo "Seeding demo MiroFish simulation fixture…"
  MIROFISH_UPLOADS=/app/uploads \
    python3 /app/scripts/seed_personal_investor_simulation.py --skip-insights
fi

exec uv run python run.py
