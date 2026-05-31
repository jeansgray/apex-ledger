"""StockTwits sentiment provider — pre-labeled Bullish/Bearish per ticker.

No API key required for public streams.
Rate limit: 200 requests/hour.
Cache TTL: 1 hour (sentiment moves fast, no point caching longer).
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import httpx

BASE_URL = "https://api.stocktwits.com/api/2/streams/symbol"
CACHE_TTL = 3600  # 1 hour


class StockTwitsClient:
    def __init__(self, cache_dir: Path | None = None) -> None:
        self.cache_dir = cache_dir or Path("./data/stocktwits_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def sentiment_summary(self, symbols: list[str], limit: int = 30) -> list[str]:
        """Return Bullish/Bearish ratio + top messages per symbol as research bullets."""
        unique = list(dict.fromkeys(
            s.upper() for s in symbols if s.upper() not in {"CASH", "USD"}
        ))
        bullets: list[str] = []
        for symbol in unique:
            result = self._fetch_symbol(symbol, limit)
            if result:
                bullets.extend(result)
        return bullets

    def _fetch_symbol(self, symbol: str, limit: int) -> list[str]:
        cache_key = f"ST_{symbol}"
        data = self._read_cache(cache_key)
        if data is None:
            try:
                headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
                with httpx.Client(timeout=5.0, headers=headers) as client:
                    response = client.get(
                        f"{BASE_URL}/{symbol}.json",
                        params={"limit": 30},
                    )
                    if response.status_code in {404, 429}:
                        return []
                    response.raise_for_status()
                    if not response.content:
                        return []
                    data = response.json()
            except Exception:
                return []
            status = data.get("response", {}).get("status")
            if status not in {200, "200"}:
                return []
            self._write_cache(cache_key, data)

        messages = data.get("messages", [])
        if not messages:
            return []

        bullish = sum(1 for m in messages if (m.get("entities", {}).get("sentiment") or {}).get("basic") == "Bullish")
        bearish = sum(1 for m in messages if (m.get("entities", {}).get("sentiment") or {}).get("basic") == "Bearish")
        total = bullish + bearish

        bullets: list[str] = []
        if total > 0:
            bull_pct = round(bullish / total * 100)
            bear_pct = round(bearish / total * 100)
            bias = "Bullish" if bullish > bearish else "Bearish" if bearish > bullish else "Neutral"
            bullets.append(
                f"[stocktwits] {symbol} retail sentiment: {bias} — "
                f"{bull_pct}% bullish / {bear_pct}% bearish ({total} tagged messages)."
            )

        # Surface top bullish and bearish message for context
        for sentiment_label, label_str in [("Bullish", "bull"), ("Bearish", "bear")]:
            for msg in messages:
                if (msg.get("entities", {}).get("sentiment") or {}).get("basic") == sentiment_label:
                    body = msg.get("body", "").replace("\n", " ").strip()
                    if body and len(body) > 10:
                        bullets.append(f"[stocktwits/{label_str}] {symbol}: \"{body[:140]}\"")
                    break

        return bullets

    def _cache_path(self, key: str) -> Path:
        safe = key.replace("/", "_")
        return self.cache_dir / f"{safe}.json"

    def _read_cache(self, key: str) -> dict[str, Any] | None:
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

    def _write_cache(self, key: str, data: dict[str, Any]) -> None:
        path = self._cache_path(key)
        try:
            path.write_text(
                json.dumps({"_cached_at": time.time(), "data": data}, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass
