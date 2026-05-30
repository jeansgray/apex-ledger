"""Integration import tests."""

from pathlib import Path

from apex_ledger.integrations.schwab_import import parse_schwab_csv


def test_parse_schwab_positions_example():
    raw = Path("examples/schwab-positions.example.csv").read_text(encoding="utf-8")
    parsed = parse_schwab_csv(raw)
    assert parsed["kind"] == "positions"
    assert len(parsed["holdings"]) == 3
    symbols = {h[0] for h in parsed["holdings"]}
    assert symbols == {"VTI", "BND", "VXUS"}
    vti = next(h for h in parsed["holdings"] if h[0] == "VTI")
    assert vti[1] == 150.0
    assert vti[2] == 32000.0
    assert vti[3] == "schwab"
