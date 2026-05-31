#!/usr/bin/env python3
"""Validate Plaid keys and upsert them into .env."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APEX_ENV = ROOT / ".env"
EXAMPLE = ROOT / ".env.example"

VALID_ENVS = ("sandbox", "production")


def _read_env(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.strip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        out[key.strip()] = value.strip()
    return out


def _upsert_env(path: Path, updates: dict[str, str]) -> None:
    lines: list[str] = []
    if path.exists():
        lines = path.read_text(encoding="utf-8").splitlines()
    remaining = set(updates)
    out: list[str] = []
    for line in lines:
        if "=" in line and not line.strip().startswith("#"):
            key = line.split("=", 1)[0].strip()
            if key in updates:
                out.append(f"{key}={updates[key]}")
                remaining.discard(key)
                continue
        out.append(line)
    for key in sorted(remaining):
        out.append(f"{key}={updates[key]}")
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def _print_env_guide(env: str) -> None:
    if env == "sandbox":
        print("Mode: SANDBOX — $0/month, unlimited test Items, fake banks only.")
        print("Link test phone: 415-555-0010 · OTP: 123456 · login: user_good / pass_good")
    else:
        print("Mode: PRODUCTION (Trial) — real banks and your real phone.")
        print("Plaid Trial: free for up to 10 connected accounts (enough for 2 users).")
        print("Use the Production secret from dashboard.plaid.com/developers/keys")
        print("Dashboard → Plans: stay on Trial until you need more than 10 Items.")


def main() -> None:
    apex = _read_env(APEX_ENV)
    if len(sys.argv) > 1:
        client_id = sys.argv[1]
    else:
        client_id = os.environ.get("PLAID_CLIENT_ID") or apex.get("PLAID_CLIENT_ID") or ""

    if len(sys.argv) > 2:
        secret = sys.argv[2]
    else:
        secret = os.environ.get("PLAID_SECRET") or apex.get("PLAID_SECRET") or ""

    if len(sys.argv) > 3:
        env = sys.argv[3].lower()
    else:
        env = (
            os.environ.get("PLAID_ENV")
            or apex.get("PLAID_ENV")
            or "sandbox"
        ).lower()

    if env == "development":
        print(
            "PLAID_ENV=development is retired (Plaid removed it June 2024).",
            file=sys.stderr,
        )
        print("Use sandbox ($0, test data) or production + Trial (real data, 10 free Items).", file=sys.stderr)
        sys.exit(1)

    if env not in VALID_ENVS:
        print(f"Invalid PLAID_ENV={env!r}. Use: sandbox | production", file=sys.stderr)
        sys.exit(1)

    if not client_id or not secret:
        print("Missing Plaid credentials.", file=sys.stderr)
        print("Keys: https://dashboard.plaid.com/developers/keys", file=sys.stderr)
        print("", file=sys.stderr)
        print("Usage:", file=sys.stderr)
        print(f"  uv run python {Path(__file__).name} <client_id> <secret> [sandbox|production]", file=sys.stderr)
        sys.exit(1)

    sys.path.insert(0, str(ROOT / "src"))
    from apex_ledger.integrations.plaid_client import PlaidClient, PlaidError

    try:
        client = PlaidClient(client_id, secret, env)
        token = client.create_link_token()
    except PlaidError as exc:
        print(f"Plaid validation failed ({env}): {exc}", file=sys.stderr)
        if env == "production":
            print("Tip: Production requires the Production secret, not the Sandbox secret.", file=sys.stderr)
        sys.exit(1)

    if not token:
        print("Plaid returned an empty link_token.", file=sys.stderr)
        sys.exit(1)

    if not APEX_ENV.exists() and EXAMPLE.exists():
        APEX_ENV.write_text(EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")

    _upsert_env(
        APEX_ENV,
        {
            "PLAID_CLIENT_ID": client_id,
            "PLAID_SECRET": secret,
            "PLAID_ENV": env,
        },
    )
    print(f"Plaid {env} keys saved to .env (link_token probe OK).")
    _print_env_guide(env)
    print("Restart: docker compose up -d --build apex")


if __name__ == "__main__":
    main()
