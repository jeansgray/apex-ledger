"""Plaid HTTP client for bank + investment sync."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import httpx

PLAID_HOSTS = {
    "sandbox": "https://sandbox.plaid.com",
    # Deprecated by Plaid (June 2024) — use sandbox or production instead.
    "development": "https://development.plaid.com",
    "production": "https://production.plaid.com",
}


class PlaidError(RuntimeError):
    pass


class PlaidClient:
    def __init__(self, client_id: str, secret: str, env: str = "sandbox") -> None:
        if not client_id or not secret:
            raise PlaidError("Plaid is not configured — set PLAID_CLIENT_ID and PLAID_SECRET in .env")
        self.client_id = client_id
        self.secret = secret
        self.base_url = PLAID_HOSTS.get(env, PLAID_HOSTS["sandbox"])

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = {"client_id": self.client_id, "secret": self.secret, **payload}
        with httpx.Client(timeout=60.0) as client:
            response = client.post(f"{self.base_url}{path}", json=body)
        data = response.json()
        if response.status_code >= 400 or data.get("error_code"):
            raise PlaidError(data.get("error_message") or data.get("error_code") or response.text)
        return data

    def create_link_token(self, user_id: str = "apex-ledger-user") -> str:
        data = self._post(
            "/link/token/create",
            {
                "user": {"client_user_id": user_id},
                "client_name": "Apex Ledger",
                "products": ["transactions", "investments"],
                "country_codes": ["US"],
                "language": "en",
            },
        )
        return data["link_token"]

    def exchange_public_token(self, public_token: str) -> tuple[str, str]:
        data = self._post("/item/public_token/exchange", {"public_token": public_token})
        return data["access_token"], data["item_id"]

    def sync_ledger_data(self, access_token: str, transaction_days: int = 90) -> dict[str, Any]:
        holdings_rows: list[tuple[str, float, float | None, str]] = []
        transactions_rows: list[tuple[str, str, float, str]] = []
        institution = ""
        account_names: dict[str, str] = {}

        try:
            inv = self._post("/investments/holdings/get", {"access_token": access_token})
            institution = inv.get("item", {}).get("institution_id", "") or institution
            account_names = {
                a["account_id"]: a.get("name") or a.get("official_name") or "brokerage"
                for a in inv.get("accounts", [])
            }
            for h in inv.get("holdings", []):
                sec = next(
                    (s for s in inv.get("securities", []) if s["security_id"] == h["security_id"]),
                    {},
                )
                symbol = (sec.get("ticker_symbol") or sec.get("name") or "").strip().upper()
                if not symbol or h.get("quantity", 0) <= 0:
                    continue
                if symbol.startswith("CUR:"):
                    symbol = "CASH"
                cost = h.get("cost_basis")
                account = account_names.get(h.get("account_id"), "brokerage")
                holdings_rows.append(
                    (symbol, float(h["quantity"]), float(cost) if cost else None, account)
                )
        except PlaidError:
            pass

        if not account_names:
            try:
                acct = self._post("/accounts/get", {"access_token": access_token})
                account_names = {
                    a["account_id"]: a.get("name") or a.get("official_name") or "account"
                    for a in acct.get("accounts", [])
                }
                institution = institution or acct.get("item", {}).get("institution_id", "")
            except PlaidError:
                pass

        transactions_rows.extend(
            self._fetch_investment_transactions(access_token, account_names, transaction_days)
        )
        transactions_rows.extend(
            self._fetch_banking_transactions(access_token, account_names)
        )

        if not holdings_rows and not transactions_rows:
            raise PlaidError(
                "No holdings or transactions returned — connect an account with "
                "transactions and/or investments enabled in Plaid Link."
            )

        return {
            "holdings": holdings_rows,
            "transactions": transactions_rows,
            "institution": institution,
        }

    def _fetch_investment_transactions(
        self,
        access_token: str,
        account_names: dict[str, str],
        days: int,
    ) -> list[tuple[str, str, float, str]]:
        rows: list[tuple[str, str, float, str]] = []
        end = date.today()
        start = end - timedelta(days=days)
        offset = 0
        while True:
            data = self._post(
                "/investments/transactions/get",
                {
                    "access_token": access_token,
                    "start_date": start.isoformat(),
                    "end_date": end.isoformat(),
                    "options": {"offset": offset, "count": 100},
                },
            )
            batch = data.get("investment_transactions", [])
            for t in batch:
                posted = t.get("date") or end.isoformat()
                name = t.get("name") or "Investment activity"
                amount = float(t.get("amount", 0))
                account = account_names.get(t.get("account_id", ""), "brokerage")
                rows.append((posted, name, -amount, account))
            total = data.get("total_investment_transactions", len(batch))
            offset += len(batch)
            if offset >= total or not batch:
                break
        return rows

    def _fetch_banking_transactions(
        self,
        access_token: str,
        account_names: dict[str, str],
    ) -> list[tuple[str, str, float, str]]:
        rows: list[tuple[str, str, float, str]] = []
        cursor: str | None = None
        while True:
            payload: dict[str, Any] = {"access_token": access_token, "count": 100}
            if cursor:
                payload["cursor"] = cursor
            data = self._post("/transactions/sync", payload)
            for t in data.get("added", []):
                posted = t.get("date") or t.get("authorized_date")
                name = t.get("merchant_name") or t.get("name") or "Transaction"
                amount = float(t.get("amount", 0))
                acct_id = t.get("account_id", "")
                account = account_names.get(acct_id, acct_id[:12] or "checking")
                rows.append((posted, name, -amount, account))
            cursor = data.get("next_cursor")
            if not data.get("has_more"):
                break
        return rows
