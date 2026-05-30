"""Council orchestrator tests."""

from apex_ledger.config import Settings
from apex_ledger.council.graph import CouncilOrchestrator


def test_council_run_without_mirofish(tmp_path):
    db = tmp_path / "ledger.db"
    settings = Settings(
        apex_ledger_db=db,
        mirofish_default_simulation_id="sim_apex_personal_investor",
        apex_use_live_simulation=False,
        apex_use_kronos=True,
    )
    orchestrator = CouncilOrchestrator(settings)
    state = orchestrator.run(
        user_question="How would a rate cut affect my ETF-heavy portfolio?",
        seed_demo=True,
    )
    assert state.status == "awaiting_human"
    assert state.scenario_brief["base"]
    assert len(state.human_gates) >= 1
    assert state.portfolio_snapshot["holdings"]
    assert state.friendly_brief.get("action_items")
    assert state.suggested_moves
    assert state.kronos_forecasts
    assert state.council_debate
    assert state.signal_agreement in {"aligned", "mixed", "narrative_only"}
    assert any(g.kind == "investment_moves" for g in state.human_gates)


def test_reconciliation_proposal_on_demo_data(tmp_path):
    db = tmp_path / "ledger.db"
    settings = Settings(apex_ledger_db=db)
    orchestrator = CouncilOrchestrator(settings)
    state = orchestrator.run(user_question="Reconcile my checking activity", seed_demo=True)
    assert any(p["suggested_category"] == "software_subscription" for p in state.reconciliation_proposals)
