#!/usr/bin/env python3
"""Import your holdings into the Apex Ledger SQLite database.

Replaces demo portfolio data so council runs use *your* symbols for forecasts and moves.

Example:
  uv run python scripts/import_personal_ledger.py examples/holdings.example.csv
  python3 scripts/import_personal_ledger.py my_holdings.csv --keep-transactions
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

try:
    from apex_ledger.config import get_settings  # noqa: E402
    from apex_ledger.ledger.store import LedgerStore  # noqa: E402
except ImportError:
    print("Run with: uv run python scripts/import_personal_ledger.py <csv>", file=sys.stderr)
    raise


def load_csv(path: Path) -> list[tuple[str, float, float | None, str]]:
    rows: list[tuple[str, float, float | None, str]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"symbol", "quantity"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            raise SystemExit(
                f"{path}: CSV must include headers at least: symbol, quantity "
                "(optional: cost_basis, account)"
            )
        for line, raw in enumerate(reader, start=2):
            symbol = (raw.get("symbol") or "").strip().upper()
            if not symbol:
                continue
            try:
                quantity = float(raw["quantity"])
            except (KeyError, ValueError) as exc:
                raise SystemExit(f"{path}:{line}: invalid quantity") from exc
            cost_raw = (raw.get("cost_basis") or "").strip()
            cost_basis = float(cost_raw) if cost_raw else None
            account = (raw.get("account") or "default").strip() or "default"
            rows.append((symbol, quantity, cost_basis, account))
    if not rows:
        raise SystemExit(f"{path}: no holdings rows found")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Import personal holdings CSV into Apex Ledger")
    parser.add_argument("csv_path", type=Path, help="CSV with symbol, quantity, cost_basis, account")
    parser.add_argument(
        "--keep-transactions",
        action="store_true",
        help="Keep existing bank transactions (default clears them with demo data)",
    )
    args = parser.parse_args()

    if not args.csv_path.is_file():
        raise SystemExit(f"File not found: {args.csv_path}")

    settings = get_settings()
    store = LedgerStore(settings.apex_ledger_db)
    rows = load_csv(args.csv_path)

    if not args.keep_transactions:
        store.clear_portfolio()

    count = store.replace_holdings(rows)
    snapshot = store.portfolio_snapshot()
    print(f"Imported {count} holding(s) into {settings.apex_ledger_db}")
    print(f"Symbols: {', '.join(h['symbol'] for h in snapshot['holdings'])}")
    print("Restart Apex (or refresh the UI) and run Analyze — forecasts target your symbols.")


if __name__ == "__main__":
    main()
