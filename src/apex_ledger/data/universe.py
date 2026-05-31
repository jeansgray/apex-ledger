"""Curated stock universe for council scanning.

These are the stocks scanned for buy recommendations every council run,
in addition to any symbols in the user's watchlist.
"""

from __future__ import annotations

# ~35 liquid, high-conviction names across sectors
CURATED_UNIVERSE: list[str] = [
    # Mega-cap tech
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA",
    # Semiconductors
    "AMD", "AVGO", "TSM", "QCOM", "INTC",
    # Financials
    "JPM", "BAC", "GS", "V", "MA",
    # Healthcare
    "UNH", "LLY", "JNJ", "ABBV",
    # Energy
    "XOM", "CVX",
    # Consumer
    "COST", "WMT", "HD",
    # Industrial / defense
    "CAT", "RTX", "LMT",
    # ETFs (broad market signals)
    "SPY", "QQQ", "VTI",
]


def full_universe(watchlist: list[str]) -> list[str]:
    """Merge curated universe with user watchlist, deduplicated."""
    seen = set()
    result = []
    for sym in CURATED_UNIVERSE + [s.upper() for s in watchlist]:
        if sym not in seen:
            seen.add(sym)
            result.append(sym)
    return result
