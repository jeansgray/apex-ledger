"""Integration tests requiring optional local MiroFish."""

import httpx
import pytest

from apex_ledger.config import Settings
from apex_ledger.mirofish.client import MiroFishClient

SIMULATION_ID = "sim_apex_personal_investor"


def _mirofish_up() -> bool:
    try:
        httpx.get("http://127.0.0.1:5001/health", timeout=1.0).raise_for_status()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _mirofish_up(), reason="MiroFish not running on :5001")


def test_mirofish_fixture_report():
    client = MiroFishClient("http://127.0.0.1:5001")
    report = client.get_report_by_simulation(SIMULATION_ID)
    assert report is not None
    assert report["simulation_id"] == SIMULATION_ID


def test_council_run_with_mirofish(tmp_path):
    settings = Settings(
        apex_ledger_db=tmp_path / "ledger.db",
        mirofish_default_simulation_id=SIMULATION_ID,
    )
    from apex_ledger.council.graph import CouncilOrchestrator

    orchestrator = CouncilOrchestrator(settings)
    state = orchestrator.run(
        user_question="How would a rate cut affect my ETF portfolio?",
        simulation_id=SIMULATION_ID,
        seed_demo=True,
    )
    assert state.status == "awaiting_human"
    assert state.simulation_insights
