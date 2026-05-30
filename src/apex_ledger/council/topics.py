"""Detect question topics and produce beginner-friendly context + actions."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class TopicInsight:
    title: str
    detail: str


@dataclass
class TopicAnalysis:
    primary_topic: str
    topic_label: str
    direct_answer: str
    research_bullets: list[str] = field(default_factory=list)
    scenario_base: str = ""
    scenario_upside: str = ""
    scenario_downside: str = ""
    action_templates: list[tuple[str, str, str]] = field(default_factory=list)
    simulation_note: str = ""


_HOUSING = re.compile(r"\b(housing|home|house|mortgage|real estate|condo|rent|buyer|seller)\b", re.I)
_FLORIDA = re.compile(r"\b(florida|fl\b|miami|tampa|orlando|jacksonville)\b", re.I)
_RATES = re.compile(r"\b(rate cut|interest rate|fed|etf|portfolio|stock|bond)\b", re.I)


def analyze_question(question: str) -> TopicAnalysis:
    q = question.strip()
    is_housing = bool(_HOUSING.search(q))
    is_florida = bool(_FLORIDA.search(q))
    is_rates = bool(_RATES.search(q))

    if is_housing and is_florida:
        return TopicAnalysis(
            primary_topic="florida_housing",
            topic_label="Florida housing",
            direct_answer=(
                "Florida is not one market — prices, insurance, and flood risk vary sharply by county "
                "(think Miami vs. Tampa vs. inland areas). Buyers lately face two big pressures: "
                "home prices that ran up in many areas, and insurance premiums that can surprise "
                "new owners. Your monthly cost is more than the mortgage — budget for property tax, "
                "homeowners + flood insurance, HOA fees, and maintenance."
            ),
            research_bullets=[
                "[fact] Florida has no state income tax, but property tax and insurance often matter more for homeowners.",
                "[fact] Coastal and flood-zone homes may require separate flood insurance on top of homeowners.",
                "[interpretation] A rate cut can help affordability slightly, but insurance and local supply often matter more in FL.",
                "[interpretation] If you plan to stay 5+ years, short-term price swings matter less than total monthly cost.",
            ],
            scenario_base=(
                "Prices stay uneven: desirable metros remain expensive, while some areas see slower growth "
                "as insurance costs push buyers inland or to newer builds."
            ),
            scenario_upside=(
                "Rates ease and inventory rises — more choice for buyers, slower price growth, "
                "better chance to negotiate credits or repairs."
            ),
            scenario_downside=(
                "Insurance spikes or storm seasons raise carrying costs; buyers pause, listings sit longer, "
                "and you need a larger emergency fund for deductibles."
            ),
            action_templates=[
                ("now", "Get insurance quotes before you fall in love with a address", "FL premiums vary wildly — ask for a quote on any serious listing zip code."),
                ("now", "Compare total monthly cost in 2–3 counties", "Use mortgage + tax + insurance + HOA — not just listing price."),
                ("soon", "Get pre-approved so you know your real budget", "A pre-approval letter also makes offers stronger when you find the right place."),
                ("consider", "Plan for maintenance and emergencies", "Set aside 1–2% of home value per year plus a storm/emergency buffer in FL."),
            ],
            simulation_note=(
                "A live MiroFish simulation will model how investors react to this Florida housing scenario."
            ),
        )

    if is_housing:
        return TopicAnalysis(
            primary_topic="housing",
            topic_label="Housing market",
            direct_answer=(
                "Whether it's a good time to buy depends on your timeline, local supply, rates, and "
                "your total monthly payment — not headlines alone. Compare rent vs. buy using all-in "
                "costs, and keep an emergency fund before stretching on a mortgage."
            ),
            research_bullets=[
                "[fact] Monthly payment = principal + interest + tax + insurance (+ HOA if applicable).",
                "[interpretation] Lower rates help affordability, but home prices and local inventory still drive deals.",
            ],
            scenario_base="Stable market: modest price moves, average time on market.",
            scenario_upside="More inventory and lower rates — better negotiating room for buyers.",
            scenario_downside="Rates stay high or local prices soft — patience and strong financing matter.",
            action_templates=[
                ("now", "Write down your must-haves vs. nice-to-haves", "Location, commute, bedrooms, yard — rank them before touring."),
                ("soon", "Calculate an all-in monthly payment you can sustain", "Include tax, insurance, and a maintenance buffer."),
                ("consider", "Interview two local agents or lenders", "Compare fees, responsiveness, and who explains numbers clearly."),
            ],
        )

    if is_rates:
        return TopicAnalysis(
            primary_topic="rates_portfolio",
            topic_label="Rates & your portfolio",
            direct_answer=(
                "When the Fed cuts rates, bond prices often rise and growth stocks may get a boost — "
                "but nothing moves in a straight line. For a simple ETF mix, the main idea is: "
                "stay diversified, don't react to one headline, and rebalance if one piece grew too big."
            ),
            research_bullets=[
                "[fact] Broad stock ETFs (like VTI) and bond ETFs (like BND) react differently to rate changes.",
                "[interpretation] A single rate cut rarely changes a long-term plan — your timeline matters more.",
            ],
            scenario_base="Mixed market: modest moves, no need for sudden changes.",
            scenario_upside="Risk assets rally as rates fall and earnings hold up.",
            scenario_downside="Inflation surprises limit bond gains and increase volatility.",
            action_templates=[
                ("soon", "Check if any one holding is more than 30–40% of your portfolio", "Rebalance slowly if you're overweight one stock or sector."),
                ("consider", "Review why you own each fund", "Match investments to when you'll need the money."),
            ],
        )

    return TopicAnalysis(
        primary_topic="general",
        topic_label="Your question",
        direct_answer=(
            "We mapped your question to your current holdings, cash records, and a what-if scenario. "
            "Use the action list below — start with anything marked 'Do first' — and adjust for your goals."
        ),
        research_bullets=[f"[focus] Your question: {q}"],
        scenario_base="Steady path — no major change required unless your goals shifted.",
        scenario_upside="Conditions improve for your main goals — stay disciplined.",
        scenario_downside="A rough patch — protect cash needs before taking risk.",
        action_templates=[
            ("soon", "Write down what decision you're trying to make", "Buy, sell, hold, or just learn — clarity prevents rushed moves."),
            ("consider", "Schedule a 20-minute monthly money review", "Same day each month: balances, bills, and one goal."),
        ],
    )
