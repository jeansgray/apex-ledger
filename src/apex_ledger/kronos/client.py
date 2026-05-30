"""HTTP client for Kronos forecast service."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx

from .models import SymbolForecast


class KronosError(RuntimeError):
    pass


class KronosClient:
    def __init__(
        self,
        base_url: str,
        timeout: float = 60.0,
        fixtures_dir: Path | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.fixtures_dir = fixtures_dir or Path("./fixtures/kronos")

    def health(self) -> dict[str, Any]:
        with httpx.Client(base_url=self.base_url, timeout=self.timeout) as client:
            response = client.get("/health")
            response.raise_for_status()
            return response.json()

    def forecast_symbols(
        self,
        symbols: list[str],
        pred_len: int = 30,
        lookback: int = 120,
    ) -> list[SymbolForecast]:
        tradable = [s.upper() for s in symbols if s.upper() not in {"CASH", "USD", ""}]
        if not tradable:
            return []

        try:
            with httpx.Client(base_url=self.base_url, timeout=self.timeout) as client:
                response = client.post(
                    "/forecast/batch",
                    json={"symbols": tradable, "pred_len": pred_len, "lookback": lookback},
                )
                response.raise_for_status()
                payload = response.json()
                rows = payload.get("data", {}).get("forecasts", [])
                return [SymbolForecast.model_validate(row) for row in rows]
        except httpx.HTTPError:
            return self._load_fixture_batch(tradable)

    def _load_fixture_batch(self, symbols: list[str]) -> list[SymbolForecast]:
        out: list[SymbolForecast] = []
        for symbol in symbols:
            path = self.fixtures_dir / f"{symbol.upper()}.json"
            if not path.exists():
                continue
            data = json.loads(path.read_text(encoding="utf-8"))
            out.append(SymbolForecast.model_validate(data))
        return out
