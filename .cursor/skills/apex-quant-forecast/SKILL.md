---
name: apex-quant-forecast
description: Run Kronos-style market forecasts on portfolio symbols and summarize direction, return, and volatility for council debate.
---

# Apex Quant Forecaster

Use when the council needs **numeric market evidence** for holdings (VTI, BND, single names).

## Inputs

- Portfolio symbols from ledger snapshot
- Horizon (default 30 sessions)

## Outputs

- Per-symbol: direction (up/down/flat), return %, volatility %, sparkline
- Citation string for suggested moves

## Boundary

Call the Kronos HTTP service (`KRONOS_BASE_URL`) — do not import Kronos Python modules into Apex core.

## Human gate

Forecasts inform moves; user approves via `investment_moves` gate — nothing trades automatically.
