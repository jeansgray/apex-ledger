# Apex Ledger — Project Sitrep

## What It Is

A **personal investor platform** — not a generic trading bot. Built for one person's portfolio. Core loop: ask a financial question → AI council debates it → you approve/reject suggested moves. Nothing trades automatically.

---

## Three-Service Architecture

| Service | Port | License | Purpose |
|---------|------|---------|---------|
| **Apex Ledger** (main repo) | `:8080` | Proprietary | FastAPI app, council orchestration, UI |
| **MiroFish** (git submodule in `vendor/`) | `:5001` | AGPL-3.0 | Social simulation backend (LLM agent personas) |
| **Kronos API** | `:5002` | MIT | Quant OHLCV forecasts |

> **AGPL boundary enforced** — Apex never imports MiroFish Python modules directly; HTTP only.

---

## The Council Pipeline

Eight agent roles run sequentially on each investor question:

1. **Ledger Steward** — loads holdings + unmatched transactions
2. **Reconciliation Proposer** → **human gate** (approve/reject before posting)
3. **Research Curator** — macro/issuer context from topic analysis
4. **Quant Forecaster** — Kronos OHLCV forecasts per symbol
5. **Scenario Cartographer** — pulls MiroFish simulation insights
6. **Signal Challenge** — quant vs. narrative agreement score
7. **Compliance Skeptic** — concentration/liquidity risk flags
8. **Scenario Synthesizer** — base/upside/downside brief → **human gate** (approve/reject suggested moves)

---

## Current Data Reality

### Kronos (Quant Forecasts)
- Pulls **live OHLCV via `yfinance`** (Yahoo Finance) ✅
- Falls back to hardcoded fixture JSONs (AAPL/VTI/BND) if yfinance fails
- Forecast model is **statistical only** — momentum + volatility math, not ML
- No awareness of upcoming earnings, news events, or fundamentals

### MiroFish (Narrative Simulation)
- **Social simulation engine** — not market sentiment analysis
- Builds synthetic investor personas (retail investors, commentators, risk-aware savers)
- Runs them through a Twitter-style simulation (5 rounds)
- Generates a report on how fictional personas *would react* to the question
- Currently running off fixture simulation (`sim_apex_personal_investor`) — no live LLM runs yet
- **Requires:** `LLM_API_KEY` (OpenAI-compatible) + `ZEP_API_KEY` (Zep Cloud) for live mode

### Research Curator
- Currently has **zero live data**
- Just echoes keyword bullets parsed from the user's question text
- This is the biggest gap in the current pipeline

---

## What MiroFish Is (and Isn't)

This is a common point of confusion — MiroFish is **not** doing market sentiment analysis.

| | MiroFish | Real Market Sentiment |
|--|---------|----------------------|
| **Data source** | Synthetic LLM personas | Real news articles (Bloomberg, Reuters, etc.) |
| **Output** | How fake investors *would react* | How real markets *are reacting* |
| **Grounded in reality?** | No — pure simulation | Yes — actual headlines + scores |
| **Requires keys?** | Yes (OpenAI + Zep) | Just a data API key |
| **Speed** | 5–15 min per run | Instant |

They are designed to **complement each other**, not replace each other:

```
Real news sentiment (e.g. Alpha Vantage)
        ↓
  feeds into the brief doc that MiroFish consumes
        ↓
  MiroFish simulates how investors react to THAT real news
        ↓
  Scenario Cartographer gets grounded narrative insights
```

Right now MiroFish is simulating reactions to the user's raw question alone — no real-world news context injected. That's the missing link.

---

## Proposed Enhancement: Real Data Layer

### Priority Order

**1. News + Sentiment (Alpha Vantage) — highest impact, do first**
- `NEWS_SENTIMENT` endpoint returns scored news articles per ticker
- Transforms the Research Curator from echoing keywords → real grounded context
- Feeds directly into MiroFish brief, making simulations reality-grounded
- Feeds into: Research Curator → MiroFish → Scenario Synthesizer

**2. Earnings Data — second priority**
- `EARNINGS` gives EPS actual vs. estimate history + upcoming earnings dates
- An upcoming earnings event completely changes how to read a momentum signal
- Compliance Skeptic should be flagging "AAPL reports in 3 weeks" as a risk factor
- Kronos's linear projection is currently blind to this
- Feeds into: Quant Forecaster context + Compliance Skeptic risk flags

**3. Company Fundamentals — third**
- `OVERVIEW` gives P/E, market cap, 52-week high/low, sector, dividend yield
- Helps the council contextualize whether momentum signals make fundamental sense
- Feeds into: Research Curator + Scenario Synthesizer

**4. Economic Indicators — fourth**
- CPI, Fed funds rate, unemployment data
- Most relevant when user asks macro questions ("how does a rate cut affect my portfolio?")
- Feeds into: Scenario Cartographer + Scenario Synthesizer

### API Call Budget (Alpha Vantage free tier = 25 calls/day)

For a 3-holding portfolio (VTI/AAPL/BND):

| Endpoint | Calls per council run |
|----------|----------------------|
| `NEWS_SENTIMENT` × 3 symbols | 3 |
| `EARNINGS` × 3 symbols | 3 |
| `OVERVIEW` × 3 symbols | 3 |
| Economic Indicators | 2–3 |
| **Total** | **~12 per run** |

Leaves ~13 calls/day headroom for dev. Caching (refresh once/day per symbol) keeps this sustainable at scale.

---

## Potential Future Integrations

### Bloomberg Terminal API
- Totally wrappable via Python `blpapi` SDK
- **Desktop API (DAPI):** requires an active Bloomberg Terminal open on the same machine (~$2k/mo subscription)
- **Server API (SAPI/B-PIPE):** enterprise feed, no terminal required — tens of thousands/month
- Gold standard for institutional-quality data
- Only makes sense if a Terminal subscription is already in place

### Other Data Sources Considered

| Source | Data | Cost |
|--------|------|------|
| **Polygon.io** | Real-time + historical OHLCV, options, news | $29–$199/mo |
| **Finnhub** | Earnings calendars, IR transcripts, sentiment | Free + paid |
| **SEC EDGAR** | 10-K, 10-Q, 8-K filings | Free, no key |
| **Seeking Alpha API** | Analyst ratings, earnings transcripts | $50–$300/mo |

---

## Python Stack

- **FastAPI + Uvicorn** — REST API
- **Pydantic v2** — models/settings
- **httpx** — HTTP client for MiroFish/Kronos
- **SQLite** — ledger storage (`./data/ledger.db`)
- **uv** — package management (Python 3.11+ required, 3.12 for MiroFish)

## Key Source Layout

```
src/apex_ledger/
  api/app.py              — FastAPI routes (council, ledger, integrations, OAuth)
  council/
    graph.py              — CouncilOrchestrator (main orchestration class)
    roster.py             — 7 council role definitions
    recommendations.py   — suggested moves builder
    brief.py              — friendly brief generator
  ledger/
    store.py              — SQLite ledger CRUD
    models.py             — Transaction, Holding models
    reconciliation.py    — category matching logic
  kronos/client.py        — Kronos forecast HTTP client
  mirofish/client.py      — MiroFish HTTP client
  integrations/           — Plaid, Schwab OAuth + CSV import
  config.py               — Settings (pydantic-settings)
  cli.py                  — CLI entry point
```

---

## Required Keys (for live mode)

| Key | Used For |
|-----|----------|
| `LLM_API_KEY` | OpenAI-compatible key for MiroFish agent personas |
| `ZEP_API_KEY` | Zep Cloud memory/knowledge graph for MiroFish |
| `ALPHA_VANTAGE_API_KEY` | *(proposed)* News, earnings, fundamentals |

> Demo mode works with **no keys** — seeded VTI/AAPL/BND portfolio with fixture data.

---

## Current Service Status

| Service | URL | Status |
|---------|-----|--------|
| **Apex Ledger UI** | http://127.0.0.1:8080 | ✅ Running |
| **Kronos API** | http://127.0.0.1:5002 | ✅ Running |
| **MiroFish** | http://127.0.0.1:5001 | ⏳ Awaiting LLM + Zep keys |

---

*Generated May 30, 2026*
