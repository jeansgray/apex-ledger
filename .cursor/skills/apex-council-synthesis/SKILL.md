---
name: apex-council-synthesis
description: >-
  Merge ledger, research, simulation, and risk outputs into one actionable brief
  with explicit human approval gates for reconciliation and scenario memos.
---

# Apex Council Synthesis

## Merge order

1. Ledger steward snapshot
2. Reconciliation proposals (if any)
3. Research curator notes
4. Scenario cartographer (base / upside / downside)
5. Compliance skeptic flags

## Deliverables

### Scenario brief
Three scenarios with one actionable takeaway each for a **personal investor**.

### Human gates

Always emit:

1. `reconciliation` gate when proposals exist
2. `scenario_brief` gate before saving a decision memo

## Tone

Clear, concise, no hype. Prefer "consider" over "you should buy/sell."
