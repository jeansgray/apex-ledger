"""SQLite ledger store for personal investor data."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path

from .models import Holding, Transaction, TransactionStatus


SCHEMA = """
CREATE TABLE IF NOT EXISTS holdings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    quantity REAL NOT NULL,
    cost_basis REAL,
    account TEXT NOT NULL DEFAULT 'default'
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    posted_on TEXT NOT NULL,
    description TEXT NOT NULL,
    amount REAL NOT NULL,
    account TEXT NOT NULL DEFAULT 'default',
    category TEXT,
    status TEXT NOT NULL DEFAULT 'unmatched',
    memo TEXT
);

CREATE TABLE IF NOT EXISTS decision_memos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    council_run_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    kind TEXT NOT NULL,
    summary TEXT NOT NULL,
    approved INTEGER NOT NULL,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL UNIQUE,
    added_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


class LedgerStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def connection(self):
        conn = self._connect()
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def seed_demo_data(self) -> None:
        """Load sample holdings and unmatched transactions for local dev."""
        with self.connection() as conn:
            if conn.execute("SELECT COUNT(*) FROM holdings").fetchone()[0]:
                return
            self._insert_demo_rows(conn)

    @staticmethod
    def _insert_demo_rows(conn: sqlite3.Connection) -> None:
        conn.executemany(
            "INSERT INTO holdings (symbol, quantity, cost_basis, account) VALUES (?, ?, ?, ?)",
            [
                ("VTI", 120.0, 28500.0, "brokerage"),
                ("AAPL", 25.0, 4200.0, "brokerage"),
                ("BND", 80.0, 6400.0, "brokerage"),
            ],
        )
        conn.executemany(
            """
            INSERT INTO transactions
            (posted_on, description, amount, account, category, status, memo)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                ("2026-05-01", "DIVIDEND VTI", 42.15, "brokerage", "dividend", "reconciled", None),
                ("2026-05-12", "ADOBE *CREATIVE CLD", -59.99, "checking", None, "unmatched", None),
                ("2026-05-18", "TRANSFER TO BROKERAGE", -500.0, "checking", None, "unmatched", None),
            ],
        )

    def clear_portfolio(self) -> None:
        with self.connection() as conn:
            conn.execute("DELETE FROM holdings")
            conn.execute("DELETE FROM transactions")

    def replace_holdings(self, rows: list[tuple[str, float, float | None, str]]) -> int:
        """Replace all holdings. Each row: symbol, quantity, cost_basis, account."""
        with self.connection() as conn:
            conn.execute("DELETE FROM holdings")
            conn.executemany(
                "INSERT INTO holdings (symbol, quantity, cost_basis, account) VALUES (?, ?, ?, ?)",
                rows,
            )
            return len(rows)

    def replace_transactions(
        self,
        rows: list[tuple[str, str, float, str]],
    ) -> int:
        """Replace all transactions. Rows: posted_on, description, amount, account."""
        with self.connection() as conn:
            conn.execute("DELETE FROM transactions")
            conn.executemany(
                """
                INSERT INTO transactions
                (posted_on, description, amount, account, category, status, memo)
                VALUES (?, ?, ?, ?, NULL, 'unmatched', 'plaid')
                """,
                rows,
            )
            return len(rows)

    def import_transactions_bulk(
        self,
        rows: list[tuple[str, str, float, str]],
    ) -> int:
        """Insert transactions if not already present. Rows: posted_on, description, amount, account."""
        inserted = 0
        with self.connection() as conn:
            existing = {
                (r[0], r[1], r[2])
                for r in conn.execute(
                    "SELECT posted_on, description, amount FROM transactions"
                ).fetchall()
            }
            for posted_on, description, amount, account in rows:
                key = (posted_on, description, amount)
                if key in existing:
                    continue
                conn.execute(
                    """
                    INSERT INTO transactions
                    (posted_on, description, amount, account, category, status, memo)
                    VALUES (?, ?, ?, ?, NULL, 'unmatched', NULL)
                    """,
                    (posted_on, description, amount, account),
                )
                existing.add(key)
                inserted += 1
        return inserted

    def is_demo_portfolio(self) -> bool:
        holdings = self.list_holdings()
        if len(holdings) != 3:
            return False
        demo = {("VTI", 120.0), ("AAPL", 25.0), ("BND", 80.0)}
        actual = {(h.symbol.upper(), h.quantity) for h in holdings}
        return actual == demo

    def list_holdings(self) -> list[Holding]:
        with self.connection() as conn:
            rows = conn.execute("SELECT * FROM holdings ORDER BY symbol").fetchall()
        return [
            Holding(
                id=row["id"],
                symbol=row["symbol"],
                quantity=row["quantity"],
                cost_basis=row["cost_basis"],
                account=row["account"],
            )
            for row in rows
        ]

    def add_holding(
        self,
        symbol: str,
        quantity: float,
        cost_basis: float | None = None,
        account: str = "default",
    ) -> int:
        with self.connection() as conn:
            cur = conn.execute(
                "INSERT INTO holdings (symbol, quantity, cost_basis, account) VALUES (?, ?, ?, ?)",
                (symbol.upper(), quantity, cost_basis, account),
            )
            return int(cur.lastrowid)

    def update_holding(
        self,
        holding_id: int,
        symbol: str,
        quantity: float,
        cost_basis: float | None = None,
        account: str = "default",
    ) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                UPDATE holdings SET symbol = ?, quantity = ?, cost_basis = ?, account = ?
                WHERE id = ?
                """,
                (symbol.upper(), quantity, cost_basis, account, holding_id),
            )

    def delete_holding(self, holding_id: int) -> None:
        with self.connection() as conn:
            conn.execute("DELETE FROM holdings WHERE id = ?", (holding_id,))

    def add_transaction(
        self,
        posted_on: date,
        description: str,
        amount: float,
        account: str = "default",
    ) -> int:
        with self.connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO transactions
                (posted_on, description, amount, account, category, status, memo)
                VALUES (?, ?, ?, ?, NULL, 'unmatched', NULL)
                """,
                (posted_on.isoformat(), description, amount, account),
            )
            return int(cur.lastrowid)

    def delete_transaction(self, transaction_id: int) -> None:
        with self.connection() as conn:
            conn.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))

    def ledger_detail(self) -> dict:
        snap = self.portfolio_snapshot()
        return {
            **snap,
            "transactions": [t.model_dump(mode="json") for t in self.list_transactions()],
            "is_demo": self.is_demo_portfolio(),
        }

    def list_transactions(self, status: TransactionStatus | None = None) -> list[Transaction]:
        query = "SELECT * FROM transactions"
        params: tuple = ()
        if status:
            query += " WHERE status = ?"
            params = (status.value,)
        query += " ORDER BY posted_on DESC, id DESC"
        with self.connection() as conn:
            rows = conn.execute(query, params).fetchall()
        return [
            Transaction(
                id=row["id"],
                posted_on=date.fromisoformat(row["posted_on"]),
                description=row["description"],
                amount=row["amount"],
                account=row["account"],
                category=row["category"],
                status=TransactionStatus(row["status"]),
                memo=row["memo"],
            )
            for row in rows
        ]

    def portfolio_snapshot(self) -> dict:
        holdings = self.list_holdings()
        unmatched = self.list_transactions(TransactionStatus.UNMATCHED)
        return {
            "holdings": [h.model_dump() for h in holdings],
            "unmatched_count": len(unmatched),
            "total_market_value_estimate": sum(
                (h.cost_basis or 0.0) for h in holdings
            ),
        }

    def apply_reconciliation(
        self,
        transaction_id: int,
        category: str,
        memo: str | None = None,
    ) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                UPDATE transactions
                SET category = ?, status = 'reconciled', memo = ?
                WHERE id = ?
                """,
                (category, memo, transaction_id),
            )

    def list_watchlist(self) -> list[str]:
        with self.connection() as conn:
            rows = conn.execute("SELECT symbol FROM watchlist ORDER BY symbol").fetchall()
        return [row["symbol"] for row in rows]

    def add_to_watchlist(self, symbol: str) -> None:
        with self.connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO watchlist (symbol) VALUES (?)",
                (symbol.upper(),),
            )

    def remove_from_watchlist(self, symbol: str) -> None:
        with self.connection() as conn:
            conn.execute("DELETE FROM watchlist WHERE symbol = ?", (symbol.upper(),))

    def record_decision_memo(
        self,
        council_run_id: str,
        kind: str,
        summary: str,
        approved: bool,
        payload: dict,
    ) -> int:
        import json

        with self.connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO decision_memos
                (council_run_id, created_at, kind, summary, approved, payload_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    council_run_id,
                    datetime.now(timezone.utc).isoformat(),
                    kind,
                    summary,
                    1 if approved else 0,
                    json.dumps(payload),
                ),
            )
            return int(cur.lastrowid)
