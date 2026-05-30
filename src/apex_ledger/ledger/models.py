"""Ledger domain models."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class TransactionStatus(str, Enum):
    UNMATCHED = "unmatched"
    PROPOSED = "proposed"
    RECONCILED = "reconciled"


class Holding(BaseModel):
    id: int | None = None
    symbol: str
    quantity: float
    cost_basis: float | None = None
    account: str = "default"


class Transaction(BaseModel):
    id: int | None = None
    posted_on: date
    description: str
    amount: float
    account: str = "default"
    category: str | None = None
    status: TransactionStatus = TransactionStatus.UNMATCHED
    memo: str | None = None


class ReconciliationProposal(BaseModel):
    transaction_id: int
    suggested_category: str
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str


class DecisionMemo(BaseModel):
    id: int | None = None
    council_run_id: str
    created_at: datetime
    kind: str
    summary: str
    approved: bool
    payload: dict
