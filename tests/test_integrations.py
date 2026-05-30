"""Integration import tests."""

from pathlib import Path

from apex_ledger.integrations.schwab_client import SchwabClient
from apex_ledger.integrations.schwab_import import parse_schwab_csv
from apex_ledger.integrations.store import IntegrationStore


def test_parse_schwab_positions_example():
    raw = Path("examples/schwab-positions.example.csv").read_text(encoding="utf-8")
    parsed = parse_schwab_csv(raw)
    assert parsed["kind"] == "positions"
    assert len(parsed["holdings"]) == 3
    symbols = {h[0] for h in parsed["holdings"]}
    assert symbols == {"VTI", "BND", "VXUS"}


def test_schwab_oauth_authorize_url():
    client = SchwabClient("app-key", "app-secret", "http://127.0.0.1:8080/oauth/schwab/callback")
    url = client.authorize_url("test-state")
    assert "api.schwabapi.com/v1/oauth/authorize" in url
    assert "client_id=app-key" in url
    assert "state=test-state" in url


def test_integration_store_oauth_state(tmp_path):
    store = IntegrationStore(tmp_path / "integrations.json")
    state = store.create_oauth_state("schwab")
    assert store.consume_oauth_state(state, "schwab") is True
    assert store.consume_oauth_state(state, "schwab") is False
