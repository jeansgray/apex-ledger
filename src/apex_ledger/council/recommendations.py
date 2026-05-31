"""Turn Kronos + MiroFish evidence into suggested investment moves."""

from __future__ import annotations

from pydantic import BaseModel, Field

from ..kronos.models import SymbolForecast
from .topics import TopicAnalysis

NON_TRADABLE = {"", "CASH", "USD", "CUR:USD"}


class SuggestedMove(BaseModel):
    action: str
    symbol: str
    title: str
    amount_usd: float | None = None
    allocation_pct: float | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str
    simulation_citation: str = ""
    kronos_citation: str = ""
    signal_agreement: str = "aligned"


def build_suggested_moves(
    topic: TopicAnalysis,
    holdings: list[dict],
    simulation_insights: list[str],
    cash_to_deploy: float = 1000.0,
    kronos_forecasts: list[SymbolForecast] | None = None,
    confidence_multiplier: float = 1.0,
    signal_agreement: str = "aligned",
) -> list[SuggestedMove]:
    insight_blob = " ".join(simulation_insights).lower()
    sim_citation = _best_citation(simulation_insights)
    forecast_map = {f.symbol.upper(): f for f in (kronos_forecasts or [])}

    def _conf(base: float) -> float:
        return round(min(0.95, max(0.45, base * confidence_multiplier)), 2)

    def _kronos_cite(symbol: str) -> str:
        f = forecast_map.get(symbol.upper())
        if not f:
            return f"No Kronos forecast for {symbol.upper()} — using portfolio context only."
        return (
            f"{f.symbol} forecast ({f.horizon_days}d): {f.direction} "
            f"{f.return_pct:+.1f}%, vol ~{f.volatility_pct:.1f}%."
        )

    portfolio_moves = _moves_from_holdings(
        holdings,
        cash_to_deploy,
        forecast_map,
        sim_citation,
        signal_agreement,
        _conf,
        _kronos_cite,
        topic,
        insight_blob,
    )
    if portfolio_moves:
        return portfolio_moves

    return _template_moves(
        topic,
        holdings,
        insight_blob,
        cash_to_deploy,
        forecast_map,
        sim_citation,
        signal_agreement,
        _conf,
        _kronos_cite,
    )


def _tradable_holdings(holdings: list[dict]) -> list[dict]:
    out: list[dict] = []
    for h in holdings:
        sym = str(h.get("symbol", "")).upper()
        if sym in NON_TRADABLE or sym.startswith("CUR:"):
            continue
        out.append(h)
    return out


def _moves_from_holdings(
    holdings: list[dict],
    cash_to_deploy: float,
    forecast_map: dict[str, SymbolForecast],
    sim_citation: str,
    signal_agreement: str,
    _conf,
    _kronos_cite,
    topic: TopicAnalysis,
    insight_blob: str,
) -> list[SuggestedMove]:
    tradable = _tradable_holdings(holdings)
    if not tradable:
        return []

    moves: list[SuggestedMove] = []
    total_qty = sum(float(h.get("quantity") or 0) for h in tradable) or 1.0

    for h in tradable:
        sym = str(h["symbol"]).upper()
        qty = float(h.get("quantity") or 0)
        weight = qty / total_qty
        f = forecast_map.get(sym)
        concentrated = weight > 0.7

        if concentrated and f and f.volatility_pct > 18:
            action = "reduce"
            title = f"Trim {sym} — {weight:.0%} of portfolio, elevated vol"
            rationale = (
                f"{sym} dominates your holdings ({qty:g} shares). Council suggests trimming "
                "single-name risk before adding more."
            )
            allocation_pct = min(25.0, weight * 100 * 0.3)
        elif f and f.direction == "down":
            action = "hold"
            title = f"Hold {sym} — forecast soft near-term"
            rationale = (
                f"Kronos sees near-term pressure on {sym}; avoid adding until trend improves."
            )
            allocation_pct = None
        elif f and f.direction == "up":
            action = "hold"
            title = f"Hold {sym} — forecast supports current position"
            rationale = f"Quant path is favorable for {sym} over the forecast horizon."
            allocation_pct = None
        else:
            action = "hold"
            title = f"Hold {sym}"
            rationale = f"Maintain {sym} ({qty:g} shares) while monitoring scenario risk."
            allocation_pct = None

        moves.append(
            SuggestedMove(
                action=action,
                symbol=sym,
                title=title,
                allocation_pct=allocation_pct,
                confidence=_conf(0.72 if action == "hold" else 0.66),
                rationale=rationale,
                simulation_citation=sim_citation,
                kronos_citation=_kronos_cite(sym),
                signal_agreement=signal_agreement,
            )
        )

    deploy = cash_to_deploy
    if topic.primary_topic in {"florida_housing", "housing"}:
        deploy *= 0.55
        moves.insert(
            0,
            SuggestedMove(
                action="allocate_cash",
                symbol="CASH",
                title="Keep a home-buying cash reserve",
                amount_usd=round(cash_to_deploy - deploy, 2),
                allocation_pct=55.0,
                confidence=_conf(0.8),
                rationale="Large near-term goal — liquidity first.",
                simulation_citation=sim_citation,
                kronos_citation="Cash reserve — not market-forecasted.",
                signal_agreement=signal_agreement,
            ),
        )

    if deploy > 0 and tradable:
        ranked = sorted(
            tradable,
            key=lambda h: forecast_map.get(str(h["symbol"]).upper()).return_pct
            if forecast_map.get(str(h["symbol"]).upper())
            else 0.0,
            reverse=True,
        )
        top = str(ranked[0]["symbol"]).upper()
        top_f = forecast_map.get(top)
        if top_f and top_f.direction == "down":
            top = str(ranked[-1]["symbol"]).upper() if len(ranked) > 1 else top

        buy_pct = 0.65 if "sticky" not in insight_blob else 0.45
        moves.insert(
            0,
            SuggestedMove(
                action="buy",
                symbol=top,
                title=f"Add ${round(deploy * buy_pct):,.0f} to {top}",
                amount_usd=round(deploy * buy_pct, 2),
                allocation_pct=buy_pct * 100,
                confidence=_conf(0.74 if top_f and top_f.direction == "up" else 0.62),
                rationale=(
                    f"Deploy new cash into {top}, a name you already hold — "
                    "aligned with your live portfolio and Kronos outlook."
                ),
                simulation_citation=sim_citation,
                kronos_citation=_kronos_cite(top),
                signal_agreement=signal_agreement,
            ),
        )

        if len(tradable) > 1 and deploy * (1 - buy_pct) >= 50:
            second = str(ranked[1]["symbol"]).upper()
            if second != top:
                moves.append(
                    SuggestedMove(
                        action="buy",
                        symbol=second,
                        title=f"Diversify — add ${round(deploy * (1 - buy_pct)):,.0f} to {second}",
                        amount_usd=round(deploy * (1 - buy_pct), 2),
                        allocation_pct=(1 - buy_pct) * 100,
                        confidence=_conf(0.64),
                        rationale="Split new money across your existing names to reduce concentration.",
                        simulation_citation=sim_citation,
                        kronos_citation=_kronos_cite(second),
                        signal_agreement=signal_agreement,
                    )
                )

    return moves


def _template_moves(
    topic: TopicAnalysis,
    holdings: list[dict],
    insight_blob: str,
    cash_to_deploy: float,
    forecast_map: dict[str, SymbolForecast],
    sim_citation: str,
    signal_agreement: str,
    _conf,
    _kronos_cite,
) -> list[SuggestedMove]:
    symbols = {h.get("symbol", "").upper() for h in holdings}
    moves: list[SuggestedMove] = []

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
                confidence=_conf(0.82),
                rationale=(
                    "Life-goal timeline favors liquidity; council keeps a large cash buffer for "
                    "down payment, insurance surprises, and closing costs."
                ),
                simulation_citation=sim_citation,
                kronos_citation="Cash bucket — no market path forecast.",
                signal_agreement=signal_agreement,
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
                    confidence=_conf(0.74),
                    rationale="Bonds dampen volatility while you approach a home purchase timeline.",
                    simulation_citation=sim_citation,
                    kronos_citation=_kronos_cite("BND"),
                    signal_agreement=signal_agreement,
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
                    confidence=_conf(0.68),
                    rationale="Small equity exposure preserves long-term growth without over-risking near-term cash needs.",
                    simulation_citation=sim_citation,
                    kronos_citation=_kronos_cite("VTI"),
                    signal_agreement=signal_agreement,
                )
            )
        if "AAPL" in symbols:
            f = forecast_map.get("AAPL")
            conf = 0.76 if not f or f.volatility_pct < 15 else 0.62
            moves.append(
                SuggestedMove(
                    action="hold",
                    symbol="AAPL",
                    title="Hold Apple — avoid adding single-stock risk pre-homebuying",
                    confidence=_conf(conf),
                    rationale="Concentrated single names add volatility while you're preparing for a large housing expense.",
                    simulation_citation=sim_citation,
                    kronos_citation=_kronos_cite("AAPL"),
                    signal_agreement=signal_agreement,
                )
            )
        return moves

    if topic.primary_topic == "rates_portfolio":
        bnd_f = forecast_map.get("BND")
        vti_f = forecast_map.get("VTI")
        bond_tilt = 0.55 if any(w in insight_blob for w in ("sticky", "inflation", "cautious", "risk")) else 0.40
        if bnd_f and bnd_f.direction == "up":
            bond_tilt = min(0.65, bond_tilt + 0.08)
        equity_tilt = 1.0 - bond_tilt
        moves.append(
            SuggestedMove(
                action="buy",
                symbol="BND",
                title="Tilt new money toward bonds if rates are falling but inflation is sticky",
                amount_usd=round(cash_to_deploy * bond_tilt, 2),
                allocation_pct=bond_tilt * 100,
                confidence=_conf(0.78),
                rationale="Council blends rate-cut positioning with inflation caution; bonds anchor the portfolio.",
                simulation_citation=sim_citation,
                kronos_citation=_kronos_cite("BND"),
                signal_agreement=signal_agreement,
            )
        )
        moves.append(
            SuggestedMove(
                action="buy",
                symbol="VTI",
                title="Maintain core equity exposure via a broad ETF",
                amount_usd=round(cash_to_deploy * equity_tilt, 2),
                allocation_pct=equity_tilt * 100,
                confidence=_conf(0.72 if not vti_f or vti_f.direction != "down" else 0.58),
                rationale="Broad market ETF keeps diversification without betting on one company.",
                simulation_citation=sim_citation,
                kronos_citation=_kronos_cite("VTI"),
                signal_agreement=signal_agreement,
            )
        )
        if "AAPL" in symbols:
            aapl_f = forecast_map.get("AAPL")
            action = "reduce" if aapl_f and aapl_f.volatility_pct > 14 else "hold"
            moves.append(
                SuggestedMove(
                    action=action,
                    symbol="AAPL",
                    title="Trim Apple if it dominates your portfolio"
                    if action == "reduce"
                    else "Hold Apple — watch concentration",
                    allocation_pct=15.0 if action == "reduce" else None,
                    confidence=_conf(0.65),
                    rationale="Rebalance single-name risk into VTI/BND when quant vol is elevated.",
                    simulation_citation=sim_citation,
                    kronos_citation=_kronos_cite("AAPL"),
                    signal_agreement=signal_agreement,
                )
            )
        return moves

    vti_tilt = 0.6
    bnd_tilt = 0.4
    vti_f = forecast_map.get("VTI")
    bnd_f = forecast_map.get("BND")
    if vti_f and bnd_f:
        if vti_f.direction == "down" and bnd_f.direction != "down":
            vti_tilt, bnd_tilt = 0.45, 0.55

    moves.append(
        SuggestedMove(
            action="buy",
            symbol="VTI",
            title="Default core: broad US market ETF",
            amount_usd=round(cash_to_deploy * vti_tilt, 2),
            allocation_pct=vti_tilt * 100,
            confidence=_conf(0.7),
            rationale="When the scenario is unclear, start with diversified equity exposure.",
            simulation_citation=sim_citation,
            kronos_citation=_kronos_cite("VTI"),
            signal_agreement=signal_agreement,
        )
    )
    moves.append(
        SuggestedMove(
            action="buy",
            symbol="BND",
            title="Balance with bonds for stability",
            amount_usd=round(cash_to_deploy * bnd_tilt, 2),
            allocation_pct=bnd_tilt * 100,
            confidence=_conf(0.68),
            rationale="Pair equities with bonds to reduce drawdown risk.",
            simulation_citation=sim_citation,
            kronos_citation=_kronos_cite("BND"),
            signal_agreement=signal_agreement,
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
        if "Live MiroFish simulation is still running" in text:
            continue
        return text[:240]
    return "Based on your question scenario and portfolio context."
