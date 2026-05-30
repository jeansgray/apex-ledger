"""Heuristic reconciliation proposals for unmatched transactions."""

from __future__ import annotations

import re

from .models import ReconciliationProposal, Transaction


_CATEGORY_RULES: tuple[tuple[re.Pattern[str], str, float], ...] = (
    (re.compile(r"ADOBE|CREATIVE", re.I), "software_subscription", 0.82),
    (re.compile(r"TRANSFER.*BROKERAGE|BROKERAGE TRANSFER", re.I), "investment_transfer", 0.78),
    (re.compile(r"DIVIDEND", re.I), "dividend", 0.9),
    (re.compile(r"AMAZON|AMZN", re.I), "shopping", 0.65),
    (re.compile(r"UBER|LYFT", re.I), "transport", 0.7),
)


def propose_reconciliation(transactions: list[Transaction]) -> list[ReconciliationProposal]:
    proposals: list[ReconciliationProposal] = []
    for txn in transactions:
        if txn.id is None:
            continue
        matched = False
        for pattern, category, confidence in _CATEGORY_RULES:
            if pattern.search(txn.description):
                proposals.append(
                    ReconciliationProposal(
                        transaction_id=txn.id,
                        suggested_category=category,
                        confidence=confidence,
                        rationale=f"Description '{txn.description}' matches pattern for {category}.",
                    )
                )
                matched = True
                break
        if not matched:
            proposals.append(
                ReconciliationProposal(
                    transaction_id=txn.id,
                    suggested_category="uncategorized",
                    confidence=0.35,
                    rationale="No rule matched; human review recommended.",
                )
            )
    return proposals
