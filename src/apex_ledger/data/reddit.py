"""Reddit social sentiment — trending stock mentions from WSB, r/stocks, r/investing.

Uses Reddit's public JSON API (no auth required for public subreddits).
Scans post titles for ticker mentions and scores by upvotes.
Cache TTL: 1 hour — social sentiment moves fast.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

import httpx

SUBREDDITS = ["wallstreetbets", "stocks", "investing"]
CACHE_TTL = 3600  # 1 hour
TICKER_RE = re.compile(r'\b([A-Z]{2,5})\b')

# Common false positives to filter out
NOT_TICKERS = {
    "I", "A", "BE", "IT", "FOR", "OR", "ARE", "AT", "IS", "THE", "TO", "IN",
    "OF", "ON", "UP", "DO", "GO", "IF", "BY", "AI", "US", "CEO", "SEC", "IPO",
    "ETF", "ATH", "DD", "WSB", "EPS", "CPI", "GDP", "IMO", "FYI", "YOLO",
    "OTC", "NYSE", "NASDAQ", "SP", "PE", "TA", "IV", "OI", "PUT", "CALL",
    "API", "USD", "UK", "EU", "FED", "IRA", "LLC", "INC", "EST", "TV", "DC",
}


class RedditSentimentClient:
    def __init__(self, cache_dir: Path | None = None) -> None:
        self.cache_dir = cache_dir or Path("./data/reddit_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def trending(self, top_n: int = 10) -> list[dict[str, Any]]:
        """Return top_n trending symbols with mention counts and sentiment.

        Each item: {"symbol": str, "mentions": int, "score": int, "sources": [str]}
        """
        counts: dict[str, dict] = {}

        for sub in SUBREDDITS:
            posts = self._fetch_subreddit(sub)
            for post in posts:
                title = post.get("title", "") + " " + post.get("selftext", "")[:200]
                ups = post.get("ups", 0)
                tickers = self._extract_tickers(title)
                for ticker in tickers:
                    if ticker not in counts:
                        counts[ticker] = {"mentions": 0, "score": 0, "sources": set()}
                    counts[ticker]["mentions"] += 1
                    counts[ticker]["score"] += max(1, ups)
                    counts[ticker]["sources"].add(f"r/{sub}")

        ranked = sorted(counts.items(), key=lambda x: x[1]["score"], reverse=True)
        return [
            {
                "symbol": sym,
                "mentions": data["mentions"],
                "score": data["score"],
                "sources": sorted(data["sources"]),
            }
            for sym, data in ranked[:top_n]
        ]

    def _extract_tickers(self, text: str) -> list[str]:
        found = TICKER_RE.findall(text)
        return [t for t in found if t not in NOT_TICKERS and len(t) >= 2]

    def _fetch_subreddit(self, sub: str) -> list[dict]:
        cached = self._read_cache(sub)
        if cached is not None:
            return cached

        try:
            with httpx.Client(
                timeout=5.0,
                headers={"User-Agent": "ApexLedger/1.0 (personal finance research)"},
            ) as client:
                r = client.get(f"https://www.reddit.com/r/{sub}/hot.json?limit=50")
                r.raise_for_status()
                posts = [p["data"] for p in r.json()["data"]["children"]]
        except Exception:
            return []

        self._write_cache(sub, posts)
        return posts

    def _cache_path(self, key: str) -> Path:
        return self.cache_dir / f"reddit_{key}.json"

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
