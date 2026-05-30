"""Parse Charles Schwab CSV exports (positions + transactions)."""

from __future__ import annotations

import csv
import io
import re
from typing import Any


def _norm_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (key or "").lower())


def _row_map(row: dict[str, str]) -> dict[str, str]:
    return {_norm_key(k): (v or "").strip() for k, v in row.items()}


def _money(value: str) -> float | None:
    cleaned = (value or "").replace("$", "").replace(",", "").replace("(", "-").replace(")", "").strip()
    if not cleaned or cleaned == "--":
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_schwab_positions_csv(raw: str) -> list[tuple[str, float, float | None, str]]:
    """Return holdings rows: symbol, quantity, cost_basis, account."""
    reader = csv.DictReader(io.StringIO(raw))
    rows: list[tuple[str, float, float | None, str]] = []
    for row in reader:
        m = _row_map(row)
        symbol = (m.get("symbol") or m.get("ticker") or "").upper()
        if not symbol or symbol in {"CASH", "TOTAL", "ACCOUNT TOTAL"}:
            continue
        qty = _money(m.get("qtyquantity") or m.get("quantity") or m.get("qty") or "")
        if qty is None or qty <= 0:
            continue
        cost = _money(m.get("costbasis") or m.get("cost basis total") or m.get("costbasis total") or "")
        rows.append((symbol, qty, cost, "schwab"))
    return rows


def parse_schwab_transactions_csv(raw: str) -> list[tuple[str, str, float, str]]:
    """Return transaction rows: posted_on, description, amount, account."""
    reader = csv.DictReader(io.StringIO(raw))
    rows: list[tuple[str, str, float, str]] = []
    for row in reader:
        m = _row_map(row)
        posted = m.get("date") or m.get("tradedate") or m.get("settledate") or ""
        if not posted:
            continue
        posted = posted.split(" ")[0]
        desc = m.get("description") or m.get("action") or "Schwab activity"
        symbol = m.get("symbol")
        if symbol:
            desc = f"{desc} {symbol}".strip()
        amount = _money(m.get("amount") or m.get("netamount") or "")
        if amount is None:
            continue
        rows.append((posted, desc, amount, "schwab"))
    return rows


def parse_schwab_csv(raw: str) -> dict[str, Any]:
    """Auto-detect Schwab positions vs transactions export."""
    sample = raw[:2000].lower()
    if "qty" in sample or "cost basis" in sample or "market value" in sample:
        holdings = parse_schwab_positions_csv(raw)
        return {"kind": "positions", "holdings": holdings, "transactions": []}
    txs = parse_schwab_transactions_csv(raw)
    if txs:
        return {"kind": "transactions", "holdings": [], "transactions": txs}
    holdings = parse_schwab_positions_csv(raw)
    if holdings:
        return {"kind": "positions", "holdings": holdings, "transactions": []}
    raise ValueError("Could not parse Schwab CSV — export Positions or Transactions from Schwab.com")
