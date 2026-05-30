#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

git submodule update --init --recursive

uv python install 3.11 3.12
uv sync --extra dev

PY312="$(uv python find 3.12)"
UV_PYTHON="$PY312" uv sync --directory vendor/mirofish/backend

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example — add LLM_API_KEY and ZEP_API_KEY for live simulations."
fi

python3 scripts/setup_mirofish.py --no-start || true

echo "Dev container ready. API keys stay in .env (not committed)."
