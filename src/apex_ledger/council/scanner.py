"""Stock universe scanner — scores and ranks buy candidates.

Scoring rubric (0–105):
  Kronos momentum direction:  up=40, flat=10, down=0
  Kronos return_pct:          scaled 0–25 (capped at 15% return)
  Finnhub analyst consensus:  strong_buy*3 + buy*1, scaled 0–25
  FinBERT news sentiment:     positive=+10, negative=-5, neutral=0 (was keyword heuristic)
  Social mentions bonus:      0–5

Top-scoring stocks become "recommended buys".
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..data.finbert import FinBertScorer
    from ..data.finnhub import FinnhubClient
    from ..data.you_search import YouSearchClient
    from ..kronos.client import KronosClient


@dataclass
class StockScore:
    symbol: str
    score: float
    direction: str = "flat"
    return_pct: float = 0.0
    horizon_days: int = 30
    analyst_note: str = ""
    top_headline: str = ""
    headline_url: str = ""
    social_mentions: int = 0
    reasoning: str = ""


def score_universe(
    symbols: list[str],
    kronos: "KronosClient",
    finnhub: "FinnhubClient",
    you_search: "YouSearchClient",
    forecast_days: int = 30,
    social_trending: list[dict] | None = None,
    finbert: "FinBertScorer | None" = None,
) -> list[StockScore]:
    """Score and rank a list of symbols. Returns sorted list, best first."""
    social_map = {item["symbol"]: item["mentions"] for item in (social_trending or [])}

    # Batch Kronos forecasts
    try:
        forecasts = {f.symbol: f for f in kronos.forecast_symbols(symbols, pred_len=forecast_days)}
    except Exception:
        forecasts = {}

    results: list[StockScore] = []

    for symbol in symbols:
        score = 0.0
        reasons = []

        # ── Kronos momentum (0–65) ──
        forecast = forecasts.get(symbol)
        direction = "flat"
        return_pct = 0.0
        horizon = forecast_days
        if forecast:
            direction = forecast.direction
            return_pct = forecast.return_pct or 0.0
            horizon = forecast.horizon_days or forecast_days
            if direction == "up":
                score += 40
                reasons.append(f"Kronos: upward momentum")
            elif direction == "flat":
                score += 10
            # Scale return pct: 15% = 25 pts
            momentum_pts = min(25, (abs(return_pct) / 15) * 25) if direction == "up" else 0
            score += momentum_pts
            if return_pct > 0:
                reasons.append(f"+{return_pct:.1f}% Kronos forecast")

        # ── Finnhub analyst consensus (0–25) ──
        analyst_note = ""
        try:
            ratings_raw = finnhub._fetch("stock/recommendation", symbol)
            if ratings_raw and isinstance(ratings_raw, list):
                latest = ratings_raw[0]
                sb = latest.get("strongBuy", 0)
                b = latest.get("buy", 0)
                h = latest.get("hold", 0)
                s = latest.get("sell", 0) + latest.get("strongSell", 0)
                total = sb + b + h + s
                if total > 0:
                    raw_pts = sb * 3 + b * 1
                    analyst_pts = min(25, (raw_pts / (total * 3)) * 25)
                    score += analyst_pts
                    bias = "Strong Buy" if sb > b else "Buy" if b > h else "Hold"
                    analyst_note = f"{sb} strong buy, {b} buy, {h} hold — {bias}"
                    if bias in ("Strong Buy", "Buy"):
                        reasons.append(f"Analysts: {bias} consensus")
        except Exception:
            pass

        # ── News + FinBERT sentiment (0–10) ──
        top_headline = ""
        headline_url = ""
        try:
            news = you_search._search(
                f"{symbol} stock analyst outlook earnings",
                cache_key=f"scan_{symbol}",
            )
            if news:
                score += 5
                top = news[0]
                top_headline = top.get("title", "")
                headline_url = top.get("url", "")
                if finbert is not None:
                    # Aggregate FinBERT sentiment across top 3 headlines
                    texts = [
                        (n.get("title", "") + " " + n.get("description", "")).strip()
                        for n in news[:3]
                    ]
                    sentiment_scores = [finbert.sentiment_float(t) for t in texts if t]
                    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
                    if avg_sentiment > 0.15:
                        pts = min(10, round(avg_sentiment * 10))
                        score += pts
                        reasons.append(f"FinBERT: positive news ({avg_sentiment:+.2f})")
                    elif avg_sentiment < -0.15:
                        score -= 5
                        reasons.append(f"FinBERT: negative news ({avg_sentiment:+.2f})")
                    else:
                        reasons.append(f"FinBERT: neutral news ({avg_sentiment:+.2f})")
                else:
                    reasons.append("News present (no FinBERT)")
        except Exception:
            pass

        # ── Social mentions bonus (0–5) ──
        mentions = social_map.get(symbol, 0)
        if mentions >= 3:
            score += 5
            reasons.append(f"Trending on social ({mentions} mentions)")
        elif mentions >= 1:
            score += 2

        results.append(StockScore(
            symbol=symbol,
            score=round(score, 1),
            direction=direction,
            return_pct=round(return_pct, 2),
            horizon_days=horizon,
            analyst_note=analyst_note,
            top_headline=top_headline,
            headline_url=headline_url,
            social_mentions=mentions,
            reasoning=". ".join(reasons) if reasons else "Neutral signals.",
        ))

    results.sort(key=lambda x: x.score, reverse=True)
    return results
