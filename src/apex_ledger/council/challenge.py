"""Council signal challenge — compare Kronos quant vs MiroFish narrative."""

from __future__ import annotations

from ..kronos.models import SymbolForecast


def mirofish_sentiment(insights: list[str]) -> str:
    blob = " ".join(insights).lower()
    bullish = sum(1 for w in ("rally", "upside", "optimism", "recovery", "gains") if w in blob)
    bearish = sum(
        1 for w in ("cautious", "risk", "drawdown", "sticky", "uncertainty", "volatility") if w in blob
    )
    if bullish > bearish + 1:
        return "bullish"
    if bearish > bullish + 1:
        return "bearish"
    return "neutral"


def kronos_portfolio_bias(forecasts: list[SymbolForecast]) -> str:
    if not forecasts:
        return "neutral"
    ups = sum(1 for f in forecasts if f.direction == "up")
    downs = sum(1 for f in forecasts if f.direction == "down")
    if ups > downs:
        return "bullish"
    if downs > ups:
        return "bearish"
    return "neutral"


def run_signal_challenge(
    forecasts: list[SymbolForecast],
    simulation_insights: list[str],
) -> tuple[list[str], str, float]:
    """Return debate lines, agreement label, confidence multiplier."""
    debate: list[str] = []
    m_sent = mirofish_sentiment(simulation_insights)
    k_bias = kronos_portfolio_bias(forecasts)

    if forecasts:
        for f in forecasts[:4]:
            debate.append(
                f"Quant Forecaster ({f.symbol}): {f.direction} "
                f"{f.return_pct:+.1f}% / {f.horizon_days}d — {f.citation[:120]}"
            )

    debate.append(f"Scenario Cartographer sentiment: {m_sent} (from MiroFish narrative).")
    debate.append(f"Quant portfolio bias: {k_bias} (from Kronos-style forecasts).")

    if not forecasts:
        debate.append("Compliance Skeptic: No quant forecasts — leaning on narrative simulation only.")
        return debate, "narrative_only", 0.85

    if m_sent == k_bias or m_sent == "neutral" or k_bias == "neutral":
        debate.append(
            "Scenario Synthesizer: Signals align — moderate confidence in suggested sizing."
        )
        return debate, "aligned", 1.0

    debate.append(
        "Compliance Skeptic: MiroFish narrative and Kronos paths disagree — "
        "trim conviction and favor diversification."
    )
    return debate, "mixed", 0.72
