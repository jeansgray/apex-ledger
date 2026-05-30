---
name: apex-ledger-read
description: >-
  Load personal investor holdings, cash movements, and unmatched transactions.
  Use when summarizing portfolio state or preparing reconciliation work.
---

# Apex Ledger Read

## Scope

Personal investor ledger only — not institutional accounting.

## Procedure

1. Load holdings (symbol, quantity, cost basis, account).
2. List transactions filtered by status (`unmatched` first).
3. Summarize:
   - Holding count and estimated cost basis total
   - Unmatched transaction count
   - Accounts in use
4. Never mutate ledger data in this skill — read-only.

## Output format

```markdown
## Portfolio snapshot
- Holdings: ...
- Unmatched transactions: N
- Accounts: ...

## Unmatched (top 5)
| Date | Description | Amount | Account |
```
