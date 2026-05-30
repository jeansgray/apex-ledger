---
name: apex-risk-check
description: >-
  Challenge portfolio concentration, liquidity, and assumption risk for a personal
  investor. Not institutional compliance review.
---

# Apex Risk Check

## Checks

1. **Concentration** — single-name or single-sector dominance
2. **Liquidity** — unreconciled cash flows distorting scenario inputs
3. **Assumption drift** — scenario claims not supported by simulation evidence
4. **Scope** — remind user this is decision support, not advice

## Output

```markdown
## Risk flags
- [severity: low|medium|high] description

## Mitigations (informational)
- ...
```

Never block the pipeline — surface flags for the synthesizer and human review.
