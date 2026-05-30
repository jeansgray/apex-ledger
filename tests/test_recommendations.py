"""Recommendation engine tests."""

from apex_ledger.council.recommendations import build_suggested_moves
from apex_ledger.council.topics import analyze_question


def test_rates_portfolio_moves():
    topic = analyze_question("How would a Fed rate cut affect my ETF-heavy portfolio?")
    moves = build_suggested_moves(
        topic,
        [{"symbol": "VTI"}, {"symbol": "BND"}, {"symbol": "AAPL"}],
        ["Simulation report summary: investors stay cautious on sticky inflation."],
        cash_to_deploy=2000.0,
    )
    assert len(moves) >= 2
    symbols = {m.symbol for m in moves}
    assert "VTI" in symbols
    assert "BND" in symbols
    assert all(m.confidence > 0 for m in moves)
    assert moves[0].simulation_citation


def test_florida_housing_moves():
    topic = analyze_question("Should I buy a house in Florida this year?")
    moves = build_suggested_moves(topic, [{"symbol": "AAPL"}], [], cash_to_deploy=5000.0)
    assert any(m.symbol == "CASH" for m in moves)
    assert any(m.action == "hold" and m.symbol == "AAPL" for m in moves)
