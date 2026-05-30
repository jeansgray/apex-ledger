"""Council signal challenge tests."""

from apex_ledger.council.challenge import run_signal_challenge
from apex_ledger.kronos.models import SymbolForecast


def test_mixed_signals_when_kronos_and_mirofish_disagree():
    forecasts = [
        SymbolForecast(
            symbol="VTI",
            direction="up",
            return_pct=2.0,
            volatility_pct=10.0,
            horizon_days=30,
            last_close=100.0,
            predicted_close=102.0,
            citation="Up forecast",
            mode="fixture",
        )
    ]
    insights = ["Investors stay cautious; sticky inflation and risk dominate."]
    debate, agreement, multiplier = run_signal_challenge(forecasts, insights)
    assert agreement == "mixed"
    assert multiplier < 1.0
    assert len(debate) >= 3


def test_aligned_signals():
    forecasts = [
        SymbolForecast(
            symbol="BND",
            direction="up",
            return_pct=1.0,
            volatility_pct=5.0,
            horizon_days=30,
            last_close=70.0,
            predicted_close=71.0,
            citation="Bond uptrend",
            mode="fixture",
        )
    ]
    insights = ["Markets rally on optimism and recovery hopes."]
    _, agreement, multiplier = run_signal_challenge(forecasts, insights)
    assert agreement == "aligned"
    assert multiplier == 1.0
