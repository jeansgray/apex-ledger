"""Shared council run state."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class HumanGate(BaseModel):
    kind: str
    summary: str
    payload: dict[str, Any] = Field(default_factory=dict)
    approved: bool | None = None


class CouncilRunState(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_question: str
    simulation_id: str | None = None

    portfolio_snapshot: dict[str, Any] = Field(default_factory=dict)
    unmatched_transactions: list[dict[str, Any]] = Field(default_factory=list)
    research_notes: list[str] = Field(default_factory=list)
    simulation_insights: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    scenario_brief: dict[str, str] = Field(default_factory=dict)
    reconciliation_proposals: list[dict[str, Any]] = Field(default_factory=list)
    human_gates: list[HumanGate] = Field(default_factory=list)
    agent_outputs: dict[str, str] = Field(default_factory=dict)
    friendly_brief: dict[str, Any] = Field(default_factory=dict)
    topic_analysis: dict[str, Any] = Field(default_factory=dict)
    suggested_moves: list[dict[str, Any]] = Field(default_factory=list)
    kronos_forecasts: list[dict[str, Any]] = Field(default_factory=list)
    council_debate: list[str] = Field(default_factory=list)
    signal_agreement: str = "aligned"
    confidence_multiplier: float = 1.0
    simulation_factory: dict[str, Any] = Field(default_factory=dict)
    cash_to_deploy: float = 1000.0
    glossary: dict[str, str] = Field(default_factory=dict)
    status: str = "running"
    error: str | None = None
