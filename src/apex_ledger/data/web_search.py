"""Compliance Web Search — regulatory, legal, and tax risk per holding.

Uses Brave Search API (free tier: 2,000 queries/month).
Get a key at https://api.search.brave.com/

Capped at MAX_SEARCHES_PER_RUN per council run to stay within free tier.
Cache TTL: 12 hours — regulatory news moves faster than fundamentals.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import httpx

BRAVE_URL = "https://api.search.brave.com/res/v1/web/search"
CACHE_TTL = 43200  # 12 hours
MAX_SEARCHES_PER_RUN = 3


class ComplianceSearchClient:
    def __init__(self, api_key: str, cache_dir: Path | None = None) -> None:
        self.api_key = api_key
        self.cache_dir = cache_dir or Path("./data/search_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def compliance_flags(self, symbols: list[str]) -> list[str]:
        """Search for regulatory, legal, and tax risks for the given symbols.

        Returns risk flag strings ready to inject into state.risk_flags.
        Capped at MAX_SEARCHES_PER_RUN total searches across all symbols.
        """
        if not self.api_key:
            return []

        unique = list(dict.fromkeys(
            s.upper() for s in symbols if s.upper() not in {"CASH", "USD", "VTI", "BND"}
        ))
        flags: list[str] = []
        searches_used = 0

        for symbol in unique:
            if searches_used >= MAX_SEARCHES_PER_RUN:
                break

            # Regulatory/legal risk search
            reg_results = self._search(
                f"{symbol} SEC enforcement regulatory investigation 2025 2026",
                cache_key=f"reg_{symbol}",
            )
            searches_used += 1
            for result in reg_results[:2]:
                title = result.get("title", "")
                desc = result.get("description", "")
                url = result.get("url", "")
                if title:
                    flags.append(
                        f"[compliance/web] {symbol} regulatory: {title}. {desc[:120]} "
                        f"Source: {url}"
                    )

            if searches_used >= MAX_SEARCHES_PER_RUN:
                break

            # Tax implications search
            tax_results = self._search(
                f"tax implications selling {symbol} stock capital gains 2025 2026",
                cache_key=f"tax_{symbol}",
            )
            searches_used += 1
            for result in tax_results[:1]:
                title = result.get("title", "")
                desc = result.get("description", "")
                if title:
                    flags.append(
                        f"[compliance/tax] {symbol}: {title}. {desc[:120]}"
                    )

        return flags

    def _search(self, query: str, cache_key: str) -> list[dict[str, Any]]:
        cached = self._read_cache(cache_key)
        if cached is not None:
            return cached

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    BRAVE_URL,
                    params={"q": query, "count": 3, "safesearch": "moderate"},
                    headers={
                        "Accept": "application/json",
                        "Accept-Encoding": "gzip",
                        "X-Subscription-Token": self.api_key,
                    },
                )
                response.raise_for_status()
                data = response.json()
        except Exception:
            return []

        results = data.get("web", {}).get("results", [])
        self._write_cache(cache_key, results)
        return results

    def _cache_path(self, key: str) -> Path:
        safe = key.replace("/", "_").replace(" ", "_")
        return self.cache_dir / f"{safe}.json"

    def _read_cache(self, key: str) -> list | None:
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

    def _write_cache(self, key: str, data: list) -> None:
        path = self._cache_path(key)
        try:
            path.write_text(
                json.dumps({"_cached_at": time.time(), "data": data}, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass
