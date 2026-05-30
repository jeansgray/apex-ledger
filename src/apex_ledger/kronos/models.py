"""Kronos forecast models."""

from __future__ import annotations

from pydantic import BaseModel, Field


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
