"""You.com Search API — live financial news per holding.

Uses the You.com Search API (v1/search) to pull real-time news from
Seeking Alpha, Motley Fool, Finbold, Yahoo Finance, and other sources.

Cache TTL: 6 hours — news moves faster than fundamentals.
Get a key at https://you.com/platform/api-keys
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import httpx

YOU_SEARCH_URL = "https://api.you.com/v1/search"
CACHE_TTL = 21600  # 6 hours
MAX_NEWS_PER_SYMBOL = 4


class YouSearchClient:
    def __init__(self, api_key: str, cache_dir: Path | None = None) -> None:
        self.api_key = api_key
        self.cache_dir = cache_dir or Path("./data/you_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def news_for_symbols(self, symbols: list[str]) -> list[str]:
        """Fetch live financial news for the given symbols.

        Returns research note strings ready to inject into state.research_notes.
        """
        if not self.api_key:
            return []

        notes: list[str] = []
        unique = list(dict.fromkeys(s.upper() for s in symbols if s.upper() not in {"CASH", "USD"}))

        for symbol in unique[:5]:
            results = self._search(
                f"{symbol} stock analyst outlook earnings news",
                cache_key=f"news_{symbol}",
            )
            for item in results[:MAX_NEWS_PER_SYMBOL]:
                title = item.get("title", "")
                desc = item.get("description", "")
                url = item.get("url", "")
                page_age = item.get("page_age", "")[:10]  # just the date
                if title:
                    notes.append(
                        f"[you.com/news] {symbol} ({page_age}): {title}. {desc[:150]} "
                        f"Source: {url}"
                    )

        return notes

    def _search(self, query: str, cache_key: str) -> list[dict[str, Any]]:
        cached = self._read_cache(cache_key)
        if cached is not None:
            return cached

        try:
            with httpx.Client(timeout=12.0) as client:
                response = client.get(
                    YOU_SEARCH_URL,
                    params={"query": query, "num_web_results": MAX_NEWS_PER_SYMBOL},
                    headers={"X-API-Key": self.api_key},
                )
                response.raise_for_status()
                data = response.json()
        except Exception:
            return []

        # Prefer news results; fall back to web results
        results = data.get("results", {})
        items = results.get("news") or results.get("web") or []
        self._write_cache(cache_key, items)
        return items

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
