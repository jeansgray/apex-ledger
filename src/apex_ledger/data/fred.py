"""FRED + yfinance macro indicator provider.

VIX and 10-year Treasury yield are pulled via yfinance (already a project dep, no key).
CPI, Fed funds rate, and unemployment require a free FRED API key:
  Sign up at https://fred.stlouisfed.org/docs/api/api_key.html (takes 30 seconds)
  Add FRED_API_KEY to .env

Cache TTL: 24 hours — macro data doesn't move intraday.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import httpx

FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"
CACHE_TTL = 86400  # 24 hours

FRED_SERIES = {
    "FEDFUNDS": ("Fed funds rate", "%"),
    "CPIAUCSL": ("CPI inflation index", " index"),
    "UNRATE": ("Unemployment rate", "%"),
}

YFINANCE_TICKERS = {
    "^VIX": ("VIX market volatility", ""),
    "^TNX": ("10-year Treasury yield", "%"),
}


class FredClient:
    def __init__(self, api_key: str = "", cache_dir: Path | None = None) -> None:
        self.api_key = api_key
        self.cache_dir = cache_dir or Path("./data/fred_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def macro_summary(self) -> list[str]:
        """Return latest macro indicator values as research bullets."""
        bullets: list[str] = []
        bullets.extend(self._yfinance_bullets())
        if self.api_key:
            bullets.extend(self._fred_bullets())
        return bullets

    def _yfinance_bullets(self) -> list[str]:
        bullets: list[str] = []
        try:
            import yfinance as yf
            for ticker, (label, unit) in YFINANCE_TICKERS.items():
                cache_key = f"YF_{ticker.replace('^','')}"
                cached = self._read_cache(cache_key)
                if cached is not None:
                    value = cached.get("value")
                else:
                    hist = yf.download(ticker, period="5d", interval="1d", progress=False, auto_adjust=True)
                    if hist.empty:
                        continue
                    # Handle MultiIndex columns (yfinance >= 0.2.x)
                    close = hist["Close"]
                    if hasattr(close, "columns"):
                        close = close.iloc[:, 0]
                    close = close.dropna()
                    if close.empty:
                        continue
                    value = round(float(close.iloc[-1]), 2)
                    self._write_cache(cache_key, {"value": value})
                if value is not None:
                    bullets.append(f"[macro] {label}: {value}{unit}.")
        except Exception:
            pass
        return bullets

    def _fred_bullets(self) -> list[str]:
        bullets: list[str] = []
        for series_id, (label, unit) in FRED_SERIES.items():
            cache_key = f"FRED_{series_id}"
            cached = self._read_cache(cache_key)
            if cached is not None:
                value = cached.get("value")
            else:
                value = self._fetch_fred(series_id)
                if value is not None:
                    self._write_cache(cache_key, {"value": value})
            if value is not None:
                bullets.append(f"[macro] {label}: {value}{unit} (FRED/{series_id}).")
        return bullets

    def _fetch_fred(self, series_id: str) -> str | None:
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(FRED_BASE, params={
                    "series_id": series_id,
                    "api_key": self.api_key,
                    "file_type": "json",
                    "limit": 5,
                    "sort_order": "desc",
                })
                response.raise_for_status()
                data = response.json()
        except Exception:
            return None
        observations = data.get("observations", [])
        for obs in observations:
            val = obs.get("value", "")
            if val and val != ".":
                return val
        return None

    def _cache_path(self, key: str) -> Path:
        safe = key.replace("^", "").replace("/", "_")
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
