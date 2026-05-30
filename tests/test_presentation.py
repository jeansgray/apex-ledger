"""Presentation layer tests."""

from apex_ledger.council.presentation import build_friendly_brief
from apex_ledger.council.state import CouncilRunState
from apex_ledger.council.topics import analyze_question


def test_friendly_brief_has_action_items():
    state = CouncilRunState(
        user_question="How would a rate cut affect my ETF portfolio?",
        portfolio_snapshot={
            "holdings": [{"symbol": "VTI", "quantity": 10, "cost_basis": 2500, "account": "brokerage"}],
            "unmatched_count": 1,
            "total_market_value_estimate": 2500,
        },
        unmatched_transactions=[
            {
                "id": 1,
                "posted_on": "2026-05-12",
                "description": "ADOBE *CREATIVE CLD",
                "amount": -59.99,
            }
        ],
        reconciliation_proposals=[
            {
                "transaction_id": 1,
                "suggested_category": "software_subscription",
                "confidence": 0.82,
                "rationale": "Looks like a subscription.",
            }
        ],
        scenario_brief={
            "base": "Steady outlook.",
            "upside": "Markets rally.",
            "downside": "Drawdown possible.",
        },
        risk_flags=["Personal investor scope: this is decision support, not investment advice."],
        human_gates=[],
    )
    brief = build_friendly_brief(state, analyze_question(state.user_question))
    assert brief.action_items
    assert brief.direct_answer
    assert brief.scenarios[0].label == "Most likely"
    assert brief.bookkeeping[0]["category_label"] == "Software subscription"
