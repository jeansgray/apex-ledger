"""Turn council output into plain-language, actionable briefs for new investors."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from .state import CouncilRunState
from .topics import TopicAnalysis, analyze_question

HOLDING_NAMES: dict[str, str] = {
    "VTI": "US stock market (broad ETF)",
    "BND": "US bonds (lower risk)",
    "AAPL": "Apple stock",
    "VOO": "S&P 500 index fund",
    "VXUS": "International stocks",
}

CATEGORY_LABELS: dict[str, str] = {
    "software_subscription": "Software subscription",
    "investment_transfer": "Transfer to investment account",
    "dividend": "Dividend income",
    "shopping": "Shopping",
    "transport": "Transport",
    "uncategorized": "Not categorized yet",
}


class ActionItem(BaseModel):
    priority: str
    title: str
    detail: str
    cta_label: str | None = None
    gate_kind: str | None = None


class FriendlyScenario(BaseModel):
    key: str
    label: str
    headline: str
    explanation: str
    what_you_might_do: str


class WatchOut(BaseModel):
    severity: str
    title: str
    detail: str
    suggestion: str


class FriendlyBrief(BaseModel):
    headline: str
    intro: str
    direct_answer: str = ""
    bottom_line: str
    suggested_moves: list[dict[str, Any]] = Field(default_factory=list)
    kronos_forecasts: list[dict[str, Any]] = Field(default_factory=list)
    council_debate: list[str] = Field(default_factory=list)
    signal_agreement: str = "aligned"
    action_items: list[ActionItem] = Field(default_factory=list)
    portfolio_summary: str = ""
    holdings: list[dict[str, Any]] = Field(default_factory=list)
    scenarios: list[FriendlyScenario] = Field(default_factory=list)
    bookkeeping: list[dict[str, Any]] = Field(default_factory=list)
    watch_outs: list[WatchOut] = Field(default_factory=list)
    insights_plain: list[str] = Field(default_factory=list)
    research_plain: list[str] = Field(default_factory=list)


def _money(amount: float) -> str:
    sign = "-" if amount < 0 else ""
    return f"{sign}${abs(amount):,.2f}"


def _confidence_label(score: float) -> str:
    if score >= 0.75:
        return "High confidence match"
    if score >= 0.5:
        return "Reasonable guess — please confirm"
    return "Low confidence — needs your eyes on it"


def build_friendly_brief(state: CouncilRunState, topic: TopicAnalysis | None = None) -> FriendlyBrief:
    topic = topic or analyze_question(state.user_question)
    snapshot = state.portfolio_snapshot
    holdings = snapshot.get("holdings", [])
    unmatched_count = snapshot.get("unmatched_count", 0)
    total_basis = snapshot.get("total_market_value_estimate", 0)

    holdings_plain = []
    for h in holdings:
        symbol = h.get("symbol", "?")
        holdings_plain.append(
            {
                "symbol": symbol,
                "name": HOLDING_NAMES.get(symbol, "Investment holding"),
                "quantity": h.get("quantity"),
                "cost_basis": h.get("cost_basis"),
                "cost_label": _money(float(h.get("cost_basis") or 0)),
                "account": h.get("account", "default").replace("_", " ").title(),
            }
        )

    portfolio_summary = (
        f"You hold {len(holdings)} investment(s) with about {_money(float(total_basis))} "
        f"recorded cost basis."
    )
    if unmatched_count:
        portfolio_summary += (
            f" {unmatched_count} bank charge(s) still need a category before your books are tidy."
        )

    scenario_labels = {
        "florida_housing": (
            ("Most likely", "Steady but uneven — shop county by county"),
            ("Best case for buyers", "More choice and negotiating power"),
            ("Worst case for buyers", "Insurance or storm costs squeeze budgets"),
        ),
        "housing": (
            ("Most likely", "A balanced market — patience pays off"),
            ("Best case for buyers", "More listings and better terms"),
            ("Worst case for buyers", "Affordability stays tight"),
        ),
    }
    labels = scenario_labels.get(
        topic.primary_topic,
        (
            ("Most likely", "Steady path — no major surprises expected"),
            ("Best case", "Markets cooperate — growth assets could do well"),
            ("Worst case", "A rough patch — drawdowns are possible"),
        ),
    )

    scenarios = [
        FriendlyScenario(
            key="base",
            label=labels[0][0],
            headline=labels[0][1],
            explanation=state.scenario_brief.get("base", topic.scenario_base),
            what_you_might_do=_scenario_action("base", topic),
        ),
        FriendlyScenario(
            key="upside",
            label=labels[1][0],
            headline=labels[1][1],
            explanation=state.scenario_brief.get("upside", topic.scenario_upside),
            what_you_might_do=_scenario_action("upside", topic),
        ),
        FriendlyScenario(
            key="downside",
            label=labels[2][0],
            headline=labels[2][1],
            explanation=state.scenario_brief.get("downside", topic.scenario_downside),
            what_you_might_do=_scenario_action("downside", topic),
        ),
    ]

    bookkeeping = []
    for proposal in state.reconciliation_proposals:
        txn = next(
            (t for t in state.unmatched_transactions if t.get("id") == proposal.get("transaction_id")),
            {},
        )
        category = proposal.get("suggested_category", "uncategorized")
        bookkeeping.append(
            {
                "transaction_id": proposal.get("transaction_id"),
                "date": txn.get("posted_on", ""),
                "description": txn.get("description", "Unknown charge"),
                "amount": txn.get("amount", 0),
                "amount_label": _money(float(txn.get("amount") or 0)),
                "category_key": category,
                "category_label": CATEGORY_LABELS.get(category, category.replace("_", " ").title()),
                "confidence": proposal.get("confidence", 0),
                "confidence_label": _confidence_label(float(proposal.get("confidence") or 0)),
                "why": proposal.get("rationale", ""),
            }
        )

    watch_outs: list[WatchOut] = []
    for flag in state.risk_flags:
        lower = flag.lower()
        if "florida" in lower or "insurance" in lower or "flood" in lower:
            watch_outs.append(
                WatchOut(
                    severity="medium",
                    title="Florida-specific costs are real",
                    detail=flag,
                    suggestion="Get insurance quotes early and budget for storm deductibles.",
                )
            )
        elif "not investment advice" in lower or "not a substitute" in lower:
            watch_outs.append(
                WatchOut(
                    severity="info",
                    title="This is guidance, not a command",
                    detail=flag,
                    suggestion="Use these ideas to think and ask questions — you decide what to do.",
                )
            )
        elif "diversification" in lower or "fewer than" in lower:
            watch_outs.append(
                WatchOut(
                    severity="medium",
                    title="Your portfolio is quite concentrated",
                    detail=flag,
                    suggestion=(
                        "Over time, consider spreading across more funds or sectors "
                        "so one company doesn't dominate."
                    ),
                )
            )
        elif "unreconciled" in lower:
            watch_outs.append(
                WatchOut(
                    severity="medium",
                    title="Uncategorized spending can skew the picture",
                    detail=flag,
                    suggestion="Approve the bookkeeping suggestions below so cash flow numbers are trustworthy.",
                )
            )
        else:
            watch_outs.append(
                WatchOut(
                    severity="low",
                    title="Something to keep in mind",
                    detail=flag,
                    suggestion="Note it and revisit when you review your portfolio.",
                )
            )

    insights_plain = []
    for insight in state.simulation_insights:
        text = insight.strip()
        if not text or "simulation is macro" in text.lower():
            continue
        if text.startswith("Timeline:"):
            insights_plain.append(text.replace("Timeline:", "Timeline —"))
        elif text.startswith("Simulation report summary:"):
            insights_plain.append(text.replace("Simulation report summary:", "From the macro simulation:"))
        elif "MiroFish unavailable" in text or "missing simulation_id" in text:
            continue
        elif text.startswith("Our scenario simulation"):
            insights_plain.append(text)
        else:
            insights_plain.append(text)

    research_plain = []
    for note in state.research_notes:
        cleaned = note.replace("[fact]", "Fact:").replace("[interpretation]", "Takeaway:").replace(
            "[portfolio]", "Your portfolio:"
        ).replace("[focus]", "Focus:")
        research_plain.append(cleaned.strip())

    action_items: list[ActionItem] = []
    for template in topic.action_templates:
        priority, title, detail = template
        action_items.append(ActionItem(priority=priority, title=title, detail=detail))

    if bookkeeping:
        action_items.append(
            ActionItem(
                priority="now",
                title=f"Categorize {len(bookkeeping)} bank charge(s)",
                detail=(
                    "Matching charges to categories keeps your spending and investing records accurate."
                ),
                cta_label="Review & approve categories",
                gate_kind="reconciliation",
            )
        )
    action_items.append(
        ActionItem(
            priority="now",
            title="Save this plan to your decision log",
            detail="Keep today's summary so you can compare when the market or your life changes.",
            cta_label="Save summary",
            gate_kind="scenario_brief",
        )
    )

    if not action_items:
        action_items.append(
            ActionItem(
                priority="now",
                title="Review the summary below",
                detail="Start with the direct answer, then work through each scenario.",
            )
        )

    if unmatched_count == 0 and not bookkeeping and topic.primary_topic not in {"florida_housing", "housing"}:
        action_items.insert(
            0,
            ActionItem(
                priority="soon",
                title="Your books look tidy",
                detail="No uncategorized charges right now. Focus on the scenario takeaways below.",
            ),
        )
    if any(w.severity == "medium" for w in watch_outs):
        action_items.append(
            ActionItem(
                priority="consider",
                title="Review diversification when you have time",
                detail="You don't need to act today — add it to your next monthly money check-in.",
            )
        )

    headline = f"{topic.topic_label}: answers for your question"
    intro = (
        f"You asked: “{state.user_question}”. "
        "Below is a plain-English answer, concrete next steps, and three ways things could play out."
    )
    if topic.primary_topic in {"florida_housing", "housing"}:
        bottom_line = (
            "These moves prioritize cash for your home goal while keeping some market exposure. "
            "Approve moves you agree with — nothing executes automatically."
        )
    elif state.suggested_moves:
        agreement_note = {
            "aligned": "Kronos forecasts and MiroFish narrative agree — ",
            "mixed": "Mixed signals between Kronos and MiroFish — ",
            "narrative_only": "MiroFish narrative only (no quant forecasts) — ",
        }.get(state.signal_agreement, "")
        bottom_line = (
            f"{agreement_note}Suggested moves blend quant + narrative evidence. "
            "Approve to save them to your decision log."
        )
    else:
        bottom_line = (
            "No rush to trade. Start with bookkeeping fixes (if any), then keep the summary that fits your situation."
        )

    return FriendlyBrief(
        headline=headline,
        intro=intro,
        direct_answer=topic.direct_answer,
        bottom_line=bottom_line,
        suggested_moves=state.suggested_moves,
        kronos_forecasts=state.kronos_forecasts,
        council_debate=state.council_debate,
        signal_agreement=state.signal_agreement,
        action_items=action_items,
        portfolio_summary=portfolio_summary,
        holdings=holdings_plain,
        scenarios=scenarios,
        bookkeeping=bookkeeping,
        watch_outs=watch_outs,
        insights_plain=insights_plain,
        research_plain=research_plain,
    )


def _scenario_action(which: str, topic: TopicAnalysis) -> str:
    if topic.primary_topic == "florida_housing":
        return {
            "base": "Tour 2–3 counties and compare all-in monthly cost, not just listing price.",
            "upside": "If inventory loosens, negotiate seller credits for insurance or repairs.",
            "downside": "Pause buying if quotes jump — widen search area or increase emergency fund first.",
        }[which]
    if topic.primary_topic == "housing":
        return {
            "base": "Track listings for 4–6 weeks before offering — learn true market speed.",
            "upside": "Make offers with financing and inspection contingencies you understand.",
            "downside": "Keep renting or saving if the numbers stop working — that's a valid win.",
        }[which]
    return {
        "base": "Stay the course unless your goals or timeline changed.",
        "upside": "Avoid chasing headlines — rebalance only if one holding dominates.",
        "downside": "Cover near-term cash needs before taking extra risk.",
    }[which]
