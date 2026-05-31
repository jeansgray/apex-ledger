"""Alpha Vantage data provider — news/sentiment, earnings, fundamentals.

Call budget: 25 requests/day on free tier.
All responses are cached to ./data/av_cache/ with a 24-hour TTL so a single
council run costs at most 3 calls per symbol (news + earnings + overview).
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import httpx

BASE_URL = "https://www.alphavantage.co/query"
CACHE_TTL = 86400  # 24 hours


class AlphaVantageClient:
    def __init__(self, api_key: str, cache_dir: Path | None = None) -> None:
        self.api_key = api_key
        self.cache_dir = cache_dir or Path("./data/av_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public methods — return formatted bullet strings for research notes
    # ------------------------------------------------------------------

    def news_sentiment(self, symbols: list[str], limit: int = 5) -> list[str]:
        """Return top news headlines + sentiment scores for the given symbols."""
        if not self.api_key or not symbols:
            return []
        unique = list(dict.fromkeys(s.upper() for s in symbols if s.upper() not in {"CASH", "USD"}))
        if not unique:
            return []
        tickers = ",".join(unique)
        cache_key = f"NEWS_SENTIMENT_{tickers}"
        data = self._read_cache(cache_key)
        if data is None:
            try:
                with httpx.Client(timeout=5.0) as client:
                    response = client.get(BASE_URL, params={
                        "function": "NEWS_SENTIMENT",
                        "tickers": tickers,
                        "limit": str(limit),
                        "sort": "LATEST",
                        "apikey": self.api_key,
                    })
                    response.raise_for_status()
                    data = response.json()
            except Exception:
                return []
            if "Note" in data or "Information" in data or "Error Message" in data:
                return []
            self._write_cache(cache_key, data)
        feed = data.get("feed", [])
        bullets: list[str] = []
        for article in feed[:limit]:
            title = article.get("title", "")
            source = article.get("source", "")
            overall = article.get("overall_sentiment_label", "")
            score = article.get("overall_sentiment_score", "")
            if title:
                sentiment_str = f"{overall} ({score:.2f})" if isinstance(score, float) else overall
                bullets.append(f"[news] {title} — {source}. Sentiment: {sentiment_str}.")
        return bullets

    def earnings_summary(self, symbol: str) -> list[str]:
        """Return latest earnings EPS actual vs estimate and upcoming date."""
        if not self.api_key:
            return []
        data = self._fetch("EARNINGS", symbol)
        bullets: list[str] = []

        quarterly = data.get("quarterlyEarnings", [])
        if quarterly:
            latest = quarterly[0]
            date = latest.get("fiscalDateEnding", "")
            reported = latest.get("reportedEPS", "")
            estimated = latest.get("estimatedEPS", "")
            surprise = latest.get("surprisePercentage", "")
            if reported and estimated:
                surprise_str = f", surprise {float(surprise):+.1f}%" if surprise else ""
                bullets.append(
                    f"[earnings] {symbol.upper()} Q ending {date}: "
                    f"reported EPS {reported} vs estimated {estimated}{surprise_str}."
                )

        annual = data.get("annualEarnings", [])
        if annual:
            last_annual = annual[0]
            yr = last_annual.get("fiscalDateEnding", "")[:4]
            eps = last_annual.get("reportedEPS", "")
            if eps:
                bullets.append(f"[earnings] {symbol.upper()} FY{yr} annual EPS: {eps}.")

        return bullets

    def overview_summary(self, symbol: str) -> list[str]:
        """Return key fundamental snapshot: P/E, 52-week range, sector, market cap."""
        if not self.api_key:
            return []
        data = self._fetch("OVERVIEW", symbol)
        if not data or "Symbol" not in data:
            return []

        bullets: list[str] = []
        name = data.get("Name", symbol)
        sector = data.get("Sector", "")
        pe = data.get("PERatio", "")
        week52_high = data.get("52WeekHigh", "")
        week52_low = data.get("52WeekLow", "")
        market_cap = data.get("MarketCapitalization", "")
        dividend_yield = data.get("DividendYield", "")
        analyst_target = data.get("AnalystTargetPrice", "")

        if sector:
            bullets.append(f"[fundamental] {name} — sector: {sector}.")
        if pe and pe != "None":
            bullets.append(f"[fundamental] {symbol.upper()} P/E ratio: {pe}.")
        if week52_high and week52_low:
            bullets.append(
                f"[fundamental] {symbol.upper()} 52-week range: ${week52_low} – ${week52_high}."
            )
        if market_cap and market_cap != "None":
            cap_b = round(int(market_cap) / 1_000_000_000, 1)
            bullets.append(f"[fundamental] {symbol.upper()} market cap: ${cap_b}B.")
        if dividend_yield and dividend_yield not in {"None", "0"}:
            pct = round(float(dividend_yield) * 100, 2)
            bullets.append(f"[fundamental] {symbol.upper()} dividend yield: {pct}%.")
        if analyst_target and analyst_target != "None":
            bullets.append(
                f"[fundamental] {symbol.upper()} analyst price target: ${analyst_target}."
            )

        return bullets

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _fetch(self, function: str, symbol: str, params: dict[str, str] | None = None) -> dict[str, Any]:
        cache_key = f"{function}_{symbol.upper()}"
        cached = self._read_cache(cache_key)
        if cached is not None:
            return cached

        query: dict[str, str] = {"function": function, "symbol": symbol, "apikey": self.api_key}
        if params:
            query.update(params)

        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(BASE_URL, params=query)
                response.raise_for_status()
                data = response.json()
        except Exception:
            return {}

        # Alpha Vantage returns error messages inside the JSON body
        if "Note" in data or "Information" in data or "Error Message" in data:
            return {}

        self._write_cache(cache_key, data)
        return data

    def _cache_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

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
