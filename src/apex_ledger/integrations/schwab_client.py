"""Charles Schwab Trader API — OAuth 2.0 + account sync."""

from __future__ import annotations

import base64
import time
from datetime import date, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx

SCHWAB_API = "https://api.schwabapi.com"


class SchwabError(RuntimeError):
    pass


class SchwabClient:
    def __init__(
        self,
        app_key: str,
        app_secret: str,
        callback_url: str,
    ) -> None:
        if not app_key or not app_secret:
            raise SchwabError(
                "Schwab is not configured — set SCHWAB_APP_KEY and SCHWAB_APP_SECRET in .env"
            )
        if not callback_url:
            raise SchwabError("Set SCHWAB_CALLBACK_URL or APEX_PUBLIC_BASE_URL in .env")
        self.app_key = app_key
        self.app_secret = app_secret
        self.callback_url = callback_url

    def authorize_url(self, state: str) -> str:
        params = urlencode(
            {
                "client_id": self.app_key,
                "redirect_uri": self.callback_url,
                "state": state,
            }
        )
        return f"{SCHWAB_API}/v1/oauth/authorize?{params}"

    def _basic_auth_header(self) -> str:
        raw = f"{self.app_key}:{self.app_secret}".encode()
        return "Basic " + base64.b64encode(raw).decode()

    def exchange_code(self, code: str) -> dict[str, Any]:
        data = self._token_request(
            {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.callback_url,
            }
        )
        return self._normalize_tokens(data)

    def refresh_tokens(self, refresh_token: str) -> dict[str, Any]:
        data = self._token_request(
            {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            }
        )
        return self._normalize_tokens(data)

    def _token_request(self, form: dict[str, str]) -> dict[str, Any]:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{SCHWAB_API}/v1/oauth/token",
                data=form,
                headers={
                    "Authorization": self._basic_auth_header(),
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )
        if response.status_code >= 400:
            raise SchwabError(response.text or "Schwab token exchange failed")
        return response.json()

    @staticmethod
    def _normalize_tokens(data: dict[str, Any]) -> dict[str, Any]:
        expires_in = int(data.get("expires_in", 1800))
        return {
            "access_token": data["access_token"],
            "refresh_token": data.get("refresh_token", ""),
            "expires_at": time.time() + expires_in - 60,
            "token_type": data.get("token_type", "Bearer"),
        }

    def ensure_access_token(self, stored: dict[str, Any]) -> str:
        if stored.get("expires_at", 0) > time.time():
            return stored["access_token"]
        if not stored.get("refresh_token"):
            raise SchwabError("Schwab session expired — connect again")
        refreshed = self.refresh_tokens(stored["refresh_token"])
        stored.update(refreshed)
        return stored["access_token"]

    def _get(self, path: str, access_token: str, params: dict | None = None) -> Any:
        with httpx.Client(timeout=60.0) as client:
            response = client.get(
                f"{SCHWAB_API}{path}",
                params=params,
                headers={"Authorization": f"Bearer {access_token}"},
            )
        if response.status_code >= 400:
            raise SchwabError(response.text or f"Schwab API error: {path}")
        return response.json()

    def sync_ledger_data(self, stored: dict[str, Any]) -> dict[str, Any]:
        access_token = self.ensure_access_token(stored)
        account_rows = self._get("/trader/v1/accounts/accountNumbers", access_token)
        holdings: list[tuple[str, float, float | None, str]] = []
        transactions: list[tuple[str, str, float, str]] = []

        end = date.today()
        start = end - timedelta(days=90)

        for row in account_rows:
            account_hash = row.get("hashValue") or row.get("accountNumber")
            if not account_hash:
                continue
            account_label = "schwab"
            detail = self._get(
                f"/trader/v1/accounts/{account_hash}",
                access_token,
                {"fields": "positions"},
            )
            securities = detail.get("securitiesAccount", {})
            positions = securities.get("positions") or []
            for pos in positions:
                instrument = pos.get("instrument") or {}
                symbol = (instrument.get("symbol") or instrument.get("underlyingSymbol") or "").upper()
                qty = float(pos.get("longQuantity") or pos.get("shortQuantity") or 0)
                if not symbol or qty <= 0:
                    continue
                avg = pos.get("averagePrice") or pos.get("averageLongPrice")
                cost = float(avg) * qty if avg else None
                holdings.append((symbol, qty, cost, account_label))

            tx_payload = self._get(
                f"/trader/v1/accounts/{account_hash}/transactions",
                access_token,
                {
                    "startDate": start.isoformat(),
                    "endDate": end.isoformat(),
                    "types": "TRADE,DIVIDEND_OR_INTEREST,ACH_RECEIPT,ACH_DISBURSEMENT",
                },
            )
            for tx in tx_payload or []:
                posted = (tx.get("transactionDate") or tx.get("tradeDate") or "")[:10]
                if not posted:
                    continue
                desc = tx.get("description") or tx.get("type") or "Schwab activity"
                amount = float(tx.get("netAmount") or tx.get("amount") or 0)
                transactions.append((posted, desc, amount, account_label))

        return {
            "holdings": holdings,
            "transactions": transactions,
            "tokens": stored,
            "accounts": len(account_rows),
        }
