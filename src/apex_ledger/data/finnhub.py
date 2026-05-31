"""Finnhub provider — analyst ratings and earnings surprises per symbol.

Free tier: 60 API calls/minute, no credit card required.
Get a key at https://finnhub.io/register
Cache TTL: 24 hours.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import httpx

BASE_URL = "https://finnhub.io/api/v1"
CACHE_TTL = 86400  # 24 hours


class FinnhubClient:
    def __init__(self, api_key: str, cache_dir: Path | None = None) -> None:
        self.api_key = api_key
        self.cache_dir = cache_dir or Path("./data/finnhub_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def analyst_ratings(self, symbol: str) -> list[str]:
        """Return latest analyst buy/hold/sell consensus for a symbol."""
        if not self.api_key:
            return []
        data = self._fetch("stock/recommendation", symbol)
        if not data or not isinstance(data, list):
            return []

        latest = data[0] if data else {}
        buy = latest.get("buy", 0)
        hold = latest.get("hold", 0)
        sell = latest.get("sell", 0)
        strong_buy = latest.get("strongBuy", 0)
        strong_sell = latest.get("strongSell", 0)
        period = latest.get("period", "")

        total = buy + hold + sell + strong_buy + strong_sell
        if total == 0:
            return []

        bulls = strong_buy + buy
        bears = strong_sell + sell
        bias = "Buy" if bulls > bears else "Sell" if bears > bulls else "Hold"

        return [
            f"[analyst] {symbol.upper()} ratings ({period}): "
            f"{strong_buy} strong buy, {buy} buy, {hold} hold, "
            f"{sell} sell, {strong_sell} strong sell — consensus {bias}."
        ]

    def earnings_surprise(self, symbol: str) -> list[str]:
        """Return last 2 quarters of EPS actual vs estimate."""
        if not self.api_key:
            return []
        data = self._fetch("stock/earnings", symbol)
        if not data or not isinstance(data, list):
            return []

        bullets: list[str] = []
        for quarter in data[:2]:
            period = quarter.get("period", "")
            actual = quarter.get("actual")
            estimate = quarter.get("estimate")
            surprise = quarter.get("surprise")
            surprise_pct = quarter.get("surprisePercent")
            if actual is not None and estimate is not None:
                surprise_str = f", surprise {surprise_pct:+.1f}%" if surprise_pct is not None else ""
                bullets.append(
                    f"[earnings] {symbol.upper()} {period}: "
                    f"EPS actual ${actual:.2f} vs estimate ${estimate:.2f}{surprise_str}."
                )
        return bullets

    def _fetch(self, endpoint: str, symbol: str) -> Any:
        cache_key = f"FH_{endpoint.replace('/', '_')}_{symbol.upper()}"
        cached = self._read_cache(cache_key)
        if cached is not None:
            return cached

        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(
                    f"{BASE_URL}/{endpoint}",
                    params={"symbol": symbol.upper(), "token": self.api_key},
                )
                response.raise_for_status()
                data = response.json()
        except Exception:
            return None

        if isinstance(data, dict) and data.get("error"):
            return None

        self._write_cache(cache_key, data)
        return data

    def _cache_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    def _read_cache(self, key: str) -> Any | None:
        path = self._cache_path(key)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if time.time() - payload.get("_cached_at", 0) < CACHE_TTL:
                return payload.get("data")
        except Exception:
            pass
        return None

    def _write_cache(self, key: str, data: Any) -> None:
        path = self._cache_path(key)
        try:
            path.write_text(
                json.dumps({"_cached_at": time.time(), "data": data}, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass
