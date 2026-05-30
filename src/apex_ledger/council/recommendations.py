"""Turn simulation evidence + portfolio into suggested investment moves."""

from __future__ import annotations

from pydantic import BaseModel, Field

from .topics import TopicAnalysis


class SuggestedMove(BaseModel):
    action: str
    symbol: str
    title: str
    amount_usd: float | None = None
    allocation_pct: float | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str
    simulation_citation: str = ""


def build_suggested_moves(
    topic: TopicAnalysis,
    holdings: list[dict],
    simulation_insights: list[str],
    cash_to_deploy: float = 1000.0,
) -> list[SuggestedMove]:
    insight_blob = " ".join(simulation_insights).lower()
    symbols = {h.get("symbol", "").upper() for h in holdings}
    moves: list[SuggestedMove] = []
    citation = _best_citation(simulation_insights)

    if topic.primary_topic in {"florida_housing", "housing"}:
        cash_pct = 0.45 if "insurance" in insight_blob or "storm" in insight_blob else 0.35
        bond_pct = 0.35
        equity_pct = 0.20
        moves.append(
            SuggestedMove(
                action="allocate_cash",
                symbol="CASH",
                title="Build a dedicated home-buying cash bucket",
                amount_usd=round(cash_to_deploy * cash_pct, 2),
                allocation_pct=cash_pct * 100,
                confidence=0.82,
                rationale=(
                    "Simulation and FL housing dynamics favor keeping a large liquid buffer for "
                    "down payment, insurance surprises, and closing costs."
                ),
                simulation_citation=citation,
            )
        )
        if "BND" in symbols or not symbols:
            moves.append(
                SuggestedMove(
                    action="buy",
                    symbol="BND",
                    title="Add to bond stability while you save",
                    amount_usd=round(cash_to_deploy * bond_pct, 2),
                    allocation_pct=bond_pct * 100,
                    confidence=0.74,
                    rationale="Bonds help dampen volatility while you approach a home purchase timeline.",
                    simulation_citation=citation,
                )
            )
        if "VTI" in symbols or not symbols:
            moves.append(
                SuggestedMove(
                    action="buy",
                    symbol="VTI",
                    title="Keep modest broad-market exposure",
                    amount_usd=round(cash_to_deploy * equity_pct, 2),
                    allocation_pct=equity_pct * 100,
                    confidence=0.68,
                    rationale="Small equity exposure preserves long-term growth without over-risking near-term cash needs.",
                    simulation_citation=citation,
                )
            )
        if "AAPL" in symbols:
            moves.append(
                SuggestedMove(
                    action="hold",
                    symbol="AAPL",
                    title="Hold Apple — avoid adding single-stock risk pre-homebuying",
                    confidence=0.76,
                    rationale="Concentrated single names add volatility while you're preparing for a large housing expense.",
                    simulation_citation=citation,
                )
            )
        return moves

    if topic.primary_topic == "rates_portfolio":
        bond_tilt = 0.55 if any(w in insight_blob for w in ("sticky", "inflation", "cautious", "risk")) else 0.40
        equity_tilt = 1.0 - bond_tilt
        moves.append(
            SuggestedMove(
                action="buy",
                symbol="BND",
                title="Tilt new money toward bonds if rates are falling but inflation is sticky",
                amount_usd=round(cash_to_deploy * bond_tilt, 2),
                allocation_pct=bond_tilt * 100,
                confidence=0.78,
                rationale="Simulation points to rate-sensitive positioning; bonds benefit from cuts but inflation caps upside.",
                simulation_citation=citation,
            )
        )
        moves.append(
            SuggestedMove(
                action="buy",
                symbol="VTI",
                title="Maintain core equity exposure via a broad ETF",
                amount_usd=round(cash_to_deploy * equity_tilt, 2),
                allocation_pct=equity_tilt * 100,
                confidence=0.72,
                rationale="Broad market ETF keeps diversification without betting on one company.",
                simulation_citation=citation,
            )
        )
        if "AAPL" in symbols:
            moves.append(
                SuggestedMove(
                    action="reduce",
                    symbol="AAPL",
                    title="Trim Apple if it dominates your portfolio",
                    allocation_pct=15.0,
                    confidence=0.65,
                    rationale="Rebalance single-name risk into VTI/BND based on simulation uncertainty.",
                    simulation_citation=citation,
                )
            )
        return moves

    moves.append(
        SuggestedMove(
            action="buy",
            symbol="VTI",
            title="Default core: broad US market ETF",
            amount_usd=round(cash_to_deploy * 0.6, 2),
            allocation_pct=60.0,
            confidence=0.7,
            rationale="When the scenario is unclear, start with diversified equity exposure.",
            simulation_citation=citation,
        )
    )
    moves.append(
        SuggestedMove(
            action="buy",
            symbol="BND",
            title="Balance with bonds for stability",
            amount_usd=round(cash_to_deploy * 0.4, 2),
            allocation_pct=40.0,
            confidence=0.68,
            rationale="Pair equities with bonds to reduce drawdown risk.",
            simulation_citation=citation,
        )
    )
    return moves


def _best_citation(insights: list[str]) -> str:
    for insight in insights:
        text = insight.strip()
        if not text or text.startswith("Our scenario simulation"):
            continue
        if "MiroFish unavailable" in text:
            continue
        return text[:240]
    return "Based on your question scenario and portfolio context."
