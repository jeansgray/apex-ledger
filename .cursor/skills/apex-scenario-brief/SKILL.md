---
name: apex-scenario-brief
description: >-
  Map base, upside, and downside scenarios using MiroFish simulation outputs
  (interviews, timeline, report) tied to the user's portfolio question.
---

# Apex Scenario Brief

## Inputs

- User question (what they want to understand)
- Portfolio snapshot (holdings, unmatched cash flows)
- MiroFish `simulation_id` (required in production)

## MiroFish lane (HTTP only)

1. Confirm simulation backend health.
2. Pull insights via batch interview and/or completed report.
3. Extract 3–5 concrete future signals — not generic market commentary.

## Output

```markdown
## Base case
...

## Upside case
...

## Downside case
...

## Simulation evidence
- ...
```

## Constraints

- Cite simulation sources when available.
- If MiroFish is unreachable, state the gap explicitly — do not invent simulation quotes.
