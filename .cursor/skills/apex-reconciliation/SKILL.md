---
name: apex-reconciliation
description: >-
  Propose categories for unmatched personal transactions with confidence and
  rationale. Requires human approval before posting to the ledger.
---

# Apex Reconciliation

## Rules

- Propose only — never auto-post reconciled entries.
- Prefer explicit merchant patterns (e.g. subscription vendors, brokerage transfers).
- Flag low-confidence matches for human review.

## Output

For each unmatched transaction return:

- `transaction_id`
- `suggested_category`
- `confidence` (0.0–1.0)
- `rationale` (one sentence)

## Human gate

After proposals, stop and ask:

> Approve these reconciliation proposals? (yes/no)

Only on approval may the orchestrator call `apply_reconciliation`.
