"""Plaid HTTP client for bank + investment sync."""

from __future__ import annotations

from typing import Any

import httpx

PLAID_HOSTS = {
    "sandbox": "https://sandbox.plaid.com",
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

    def sync_ledger_data(self, access_token: str) -> dict[str, Any]:
        holdings_rows: list[tuple[str, float, float | None, str]] = []
        transactions_rows: list[tuple[str, str, float, str]] = []

        inv = self._post("/investments/holdings/get", {"access_token": access_token})
        account_names = {a["account_id"]: a.get("name") or a.get("official_name") or "brokerage"
                         for a in inv.get("accounts", [])}
        for h in inv.get("holdings", []):
            sec = next((s for s in inv.get("securities", []) if s["security_id"] == h["security_id"]), {})
            symbol = (sec.get("ticker_symbol") or sec.get("name") or "").strip().upper()
            if not symbol or h.get("quantity", 0) <= 0:
                continue
            cost = h.get("cost_basis")
            account = account_names.get(h.get("account_id"), "schwab" if "schwab" in str(account_names).lower() else "brokerage")
            holdings_rows.append((symbol, float(h["quantity"]), float(cost) if cost else None, account))

        tx = self._post(
            "/transactions/sync",
            {"access_token": access_token, "count": 100},
        )
        for t in tx.get("added", []):
            posted = t.get("date") or t.get("authorized_date")
            name = t.get("merchant_name") or t.get("name") or "Transaction"
            amount = float(t.get("amount", 0))
            # Plaid amounts: positive = money out of account; flip for our ledger convention
            transactions_rows.append((posted, name, -amount, t.get("account_id", "checking")))

        return {
            "holdings": holdings_rows,
            "transactions": transactions_rows,
            "institution": inv.get("item", {}).get("institution_id", ""),
        }
