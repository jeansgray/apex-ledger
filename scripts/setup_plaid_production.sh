#!/usr/bin/env bash
# Switch Apex Ledger to Plaid Production (Trial plan) and optionally sync keys from Plaid CLI.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Plaid Production (Trial) setup for Apex Ledger"
echo ""

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew not found. Install it first (one-time, needs admin password):"
  echo '  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
  echo "Then follow the shell PATH instructions Homebrew prints."
  exit 1
fi

if ! command -v plaid >/dev/null 2>&1; then
  echo "Installing Plaid CLI..."
  brew install plaid/plaid-cli/plaid
fi

plaid --version
echo ""

# Load existing client id from .env if present
CLIENT_ID="${PLAID_CLIENT_ID:-}"
if [[ -z "$CLIENT_ID" && -f .env ]]; then
  CLIENT_ID="$(grep -E '^PLAID_CLIENT_ID=' .env | cut -d= -f2- | tr -d '"' || true)"
fi

if [[ -z "$CLIENT_ID" ]]; then
  echo "Set PLAID_CLIENT_ID in .env or export PLAID_CLIENT_ID, then re-run."
  exit 1
fi

echo "Plaid CLI — log in and fetch Production keys (opens browser if needed):"
echo "  plaid login"
echo "  plaid keys fetch"
echo "  plaid config set --env production"
echo ""
read -r -p "Run 'plaid login' now? [y/N] " ans
if [[ "${ans,,}" == "y" ]]; then
  plaid login
  plaid keys fetch
  plaid config set --env production
fi

SECRET="${PLAID_PRODUCTION_SECRET:-}"
if [[ -z "$SECRET" ]]; then
  echo ""
  echo "Paste your Production secret (dashboard.plaid.com → Keys → Production)."
  echo "Or export PLAID_PRODUCTION_SECRET and re-run."
  read -r -s -p "Production secret: " SECRET
  echo ""
fi

if [[ -z "$SECRET" ]]; then
  echo "No secret provided."
  exit 1
fi

uv run python scripts/configure_plaid.py "$CLIENT_ID" "$SECRET" production

export PATH="${HOME}/Applications/Docker.app/Contents/Resources/bin:${PATH}"
docker compose up -d --build apex

echo ""
echo "Done. Open http://127.0.0.1:8080 → Connect bank (real phone + real bank)."
echo "Trial plan: free for up to 10 linked accounts."
