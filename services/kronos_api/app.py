"""Kronos forecast API — HTTP boundary for Apex Ledger (MIT Kronos or statistical fallback)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pandas as pd
import yfinance as yf
from fastapi import FastAPI
from pydantic import BaseModel, Field

FIXTURES_DIR = Path(os.environ.get("KRONOS_FIXTURES_DIR", "./fixtures/kronos"))
DEFAULT_LOOKBACK = 120
DEFAULT_PRED_LEN = 30

app = FastAPI(title="Apex Kronos API", version="0.1.0")


class ForecastRequest(BaseModel):
    symbols: list[str] = Field(min_length=1)
    pred_len: int = Field(default=DEFAULT_PRED_LEN, ge=5, le=120)
    lookback: int = Field(default=DEFAULT_LOOKBACK, ge=30, le=512)


class SymbolForecast(BaseModel):
    symbol: str
    direction: str
    return_pct: float
    volatility_pct: float
    horizon_days: int
    last_close: float
    predicted_close: float
    citation: str
    mode: str
    sparkline: list[float] = Field(default_factory=list)


def _load_fixture(symbol: str) -> SymbolForecast | None:
    path = FIXTURES_DIR / f"{symbol.upper()}.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return SymbolForecast.model_validate(data)


def _direction_from_return(return_pct: float) -> str:
    if return_pct > 1.0:
        return "up"
    if return_pct < -1.0:
        return "down"
    return "flat"


def _statistical_forecast(symbol: str, pred_len: int, lookback: int) -> SymbolForecast | None:
    try:
        df = yf.download(
            symbol,
            period=f"{max(lookback + pred_len, 180)}d",
            interval="1d",
            progress=False,
            auto_adjust=True,
        )
    except Exception:
        return None
    if df is None or df.empty or "Close" not in df.columns:
        return None

    closes = df["Close"].dropna()
    if len(closes) < 30:
        return None

    recent = closes.tail(lookback)
    last_close = float(recent.iloc[-1])
    mean_20 = float(recent.tail(20).mean())
    mean_60 = float(recent.tail(min(60, len(recent))).mean())
    momentum = (last_close / mean_20 - 1.0) * 0.35 + (last_close / mean_60 - 1.0) * 0.15
    daily_returns = recent.pct_change().dropna()
    vol_daily = float(daily_returns.std()) if len(daily_returns) > 5 else 0.01
    vol_pct = vol_daily * (pred_len**0.5) * 100
    return_pct = momentum * 100 * (pred_len / 30)
    predicted_close = last_close * (1 + return_pct / 100)
    direction = _direction_from_return(return_pct)

    hist = [round(float(x), 2) for x in recent.tail(10).tolist()]
    step = (predicted_close - last_close) / max(pred_len, 1)
    projected = [round(last_close + step * i, 2) for i in range(1, 11)]

    return SymbolForecast(
        symbol=symbol.upper(),
        direction=direction,
        return_pct=round(return_pct, 2),
        volatility_pct=round(vol_pct, 2),
        horizon_days=pred_len,
        last_close=round(last_close, 2),
        predicted_close=round(predicted_close, 2),
        citation=(
            f"Statistical forecast ({pred_len}d): {direction} bias "
            f"{return_pct:+.1f}% return, vol ~{vol_pct:.1f}%."
        ),
        mode="statistical",
        sparkline=hist + projected,
    )


def _forecast_symbol(symbol: str, pred_len: int, lookback: int) -> SymbolForecast:
    sym = symbol.upper()
    if sym in {"CASH", "USD"}:
        return SymbolForecast(
            symbol=sym,
            direction="flat",
            return_pct=0.0,
            volatility_pct=0.0,
            horizon_days=pred_len,
            last_close=1.0,
            predicted_close=1.0,
            citation="Cash has no market forecast path.",
            mode="cash",
            sparkline=[1.0] * 10,
        )

    use_fixture_only = os.environ.get("KRONOS_FIXTURE_ONLY", "").lower() in {"1", "true", "yes"}
    if not use_fixture_only:
        live = _statistical_forecast(sym, pred_len, lookback)
        if live:
            return live

    fixture = _load_fixture(sym)
    if fixture:
        return fixture

    return SymbolForecast(
        symbol=sym,
        direction="flat",
        return_pct=0.0,
        volatility_pct=0.0,
        horizon_days=pred_len,
        last_close=0.0,
        predicted_close=0.0,
        citation=f"No forecast data available for {sym}.",
        mode="unavailable",
        sparkline=[],
    )


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "kronos-api",
        "fixtures_dir": str(FIXTURES_DIR),
        "fixture_only": os.environ.get("KRONOS_FIXTURE_ONLY", "false"),
    }


@app.post("/forecast/batch")
def forecast_batch(body: ForecastRequest) -> dict[str, Any]:
    forecasts = [
        _forecast_symbol(symbol, body.pred_len, body.lookback).model_dump()
        for symbol in body.symbols
    ]
    return {"success": True, "data": {"forecasts": forecasts}}
