# Apex Ledger

Personal investor platform: **Kronos quant forecasts** + **MiroFish narrative simulation** + **council debate**, with Robinhood-style **suggested moves** and human approval gates.

Built for a single investor (holdings, cash goals, life questions) — not a generic trading bot.

See [SECURITY.md](SECURITY.md) for vulnerability reporting and security review skills.

## Prerequisites (read this first)

Your friend (or future you) needs all of the following before the app works end-to-end.

### System tools

| Tool | Version | Why |
|------|---------|-----|
| **Git** | any recent | clone + submodule |
| **uv** | latest | Python deps for Apex + MiroFish |
| **Python** | 3.11+ (Apex), **3.12** (MiroFish backend) | MiroFish requires `<3.13` |
| **Node.js** | 18+ | MiroFish frontend tooling (optional for Apex-only dev) |

Install Python 3.12 for MiroFish:

```bash
uv python install 3.12
```

### API keys (live simulations)

**Demo mode** works without keys (seeded fixture `sim_apex_personal_investor`). **Live MiroFish simulations** need two keys. Additional data provider keys are optional but improve council quality:

| Variable | Where to get it | Required | Used for |
|----------|-----------------|----------|----------|
| `LLM_API_KEY` | [OpenAI API keys](https://platform.openai.com/api-keys) (`sk-...`) | Yes (live sim) | MiroFish agents + ontology |
| `ZEP_API_KEY` | [Zep Cloud](https://app.getzep.com/) (free tier OK) | Yes (live sim) | MiroFish knowledge graph / memory |
| `ALPHA_VANTAGE_API_KEY` | [Alpha Vantage](https://www.alphavantage.co/support/#api-key) (free) | No | News sentiment, earnings, fundamentals per holding |
| `FINNHUB_API_KEY` | [Finnhub](https://finnhub.io/register) (free tier) | No | Analyst ratings, earnings surprises per holding |
| `FRED_API_KEY` | [FRED](https://fred.stlouisfed.org/docs/api/api_key.html) (free) | No | CPI, Fed funds rate, unemployment (VIX/Treasury free without key) |
| `SEARCH_API_KEY` | [Brave Search](https://api.search.brave.com/) (free tier) | No | Compliance web search — regulatory/legal risk per holding *(roadmap)* |

**Never commit keys.** Copy `.env.example` → `.env`, paste keys there, then sync:

```bash
cp .env.example .env
# edit .env — add LLM_API_KEY and ZEP_API_KEY
python3 scripts/configure_keys.py   # writes ~/.config/apex-ledger/mirofish.env + vendor/mirofish/.env
```

Restart both services after changing keys.

### Cursor MCP (for contributors using Cursor)

To plan issues, MRs, and pipelines from the editor:

1. **GitLab plugin** — Cursor → **Settings → Tools & MCP → GitLab** → sign in (OAuth) or use a PAT.
2. **Git MCP** — optional local repo tools (`user-git` server pointing at this clone).
3. **Restart Cursor** after changing MCP config.

Details: [SETUP.md](SETUP.md) and [GITLAB_SETUP.md](GITLAB_SETUP.md).

### Repository access

| Remote | URL |
|--------|-----|
| **GitLab** (primary) | https://gitlab.com/jeansgray/apex-ledger |
| **GitHub** (mirror, CI, Pages docs) | https://github.com/jeansgray/apex-ledger |

Clone with submodule:

```bash
git clone --recurse-submodules https://gitlab.com/jeansgray/apex-ledger.git
# or: git clone --recurse-submodules https://github.com/jeansgray/apex-ledger.git
```

Ask the owner for **Developer** access if the project is private. Static onboarding site (not the council UI): GitHub Pages from `docs/` after enabling Pages in repo settings.

---

## Repository layout

| Path | Purpose |
|------|---------|
| `src/apex_ledger/` | Proprietary Python app (FastAPI, council, ledger, MiroFish client) |
| `src/apex_ledger/web/` | Beginner-friendly UI + suggested moves panel |
| `.cursor/skills/` | Apex Council skills (Cursor + runtime discovery) |
| `skills/manifest.json` | Curated SkillMD imports |
| `vendor/mirofish/` | Git submodule — AGPL-3.0 simulation backend (**HTTP only**) |
| `scripts/configure_keys.py` | Sync LLM + Zep keys into MiroFish env files |
| `scripts/setup_mirofish.py` | Install deps, seed fixture sim, create secrets template |

## AGPL boundary

Do **not** import MiroFish Python modules into `src/apex_ledger/`. Run MiroFish as a separate service and call it over HTTP (`MIROFISH_BASE_URL`).

## Docker Compose quick start

Install [Docker Desktop](https://docs.docker.com/desktop/setup/install/mac-install/) (Mac/Windows/Linux), then from the repo root:

```bash
git clone --recurse-submodules https://gitlab.com/jeansgray/apex-ledger.git
cd apex-ledger
# already cloned without submodules?
git submodule update --init --recursive

cp .env.example .env
docker compose up --build
```

Open **http://127.0.0.1:8080** (Apex council UI). Backends: MiroFish **:5001** (AGPL, narrative sim) and Kronos API **:5002** (MIT, quant forecasts).

| Mode | Keys in `.env` | What you get |
|------|----------------|--------------|
| **Demo** (default) | leave `LLM_API_KEY` / `ZEP_API_KEY` empty | Full council UI + seeded fixture `sim_apex_personal_investor` (read-only sim APIs) |
| **Live sim** | real `LLM_API_KEY` + `ZEP_API_KEY` | Background MiroFish runs for new topics (5–15 min); add keys to `.env` then `docker compose up --build` |

Demo fixtures auto-seed on first container start (`data/` ledger + MiroFish uploads). Optional host-side re-seed:

```bash
python3 scripts/setup_mirofish.py --no-start   # or: python3 scripts/seed_personal_investor_simulation.py
```

For **live** keys when running locally (non-Docker), also run `python3 scripts/configure_keys.py` — it syncs into `vendor/mirofish/.env`. In Docker, `.env` is injected via `env_file`; editing `.env` and restarting is enough.

Stop: `docker compose down`. Ledger SQLite persists in `./data/ledger.db`.

See [SETUP.md](SETUP.md) for the full checklist (keys, persistence, healthchecks).

## Quick start (uv, local)

```bash
cd ~/Projects/apex-ledger
git submodule update --init --recursive
cp .env.example .env

# Optional but recommended for live sims — add keys to .env, then:
python3 scripts/configure_keys.py

# 2) Kronos API (terminal 1)
python3 scripts/run_kronos_api.py
# → http://127.0.0.1:5002

# 3) MiroFish backend (terminal 2)
uv sync
python3 scripts/setup_mirofish.py
UV_PYTHON=$(uv python find 3.12) uv run --directory vendor/mirofish/backend python run.py
# → http://127.0.0.1:5001

# 4) Apex Ledger (terminal 3)
uv sync --extra dev
uv run apex-ledger serve --port 8080
# → http://127.0.0.1:8080
```

CLI smoke test:

```bash
uv run apex-ledger council-run "How would a Fed rate cut affect my ETF-heavy portfolio?"
```

### What to expect in the UI

- **Same dashboard everywhere** when all three services run (Docker Compose = recommended). Dev container and manual uv need Kronos on `:5002` too — otherwise forecasts degrade to fixtures.
- **Suggested moves** — quant + narrative evidence; approve to save (nothing trades automatically).
- **Live simulation** — with LLM + Zep keys, new topics spawn background MiroFish runs (5–15 min).
- **Demo portfolio by default** — VTI/AAPL/BND seeded into `./data/ledger.db`. Replace with your holdings:

```bash
cp examples/holdings.example.csv my_holdings.csv
# edit symbols/quantities, then:
python3 scripts/import_personal_ledger.py my_holdings.csv
```

See [SETUP.md §9 Personal portfolio](SETUP.md#9-personal-portfolio-replace-demo-data).

## Apex Council (personal investor)

| Role | Lane |
|------|------|
| Ledger Steward | Holdings + unmatched transactions |
| Reconciliation Proposer | Category proposals → **human gate** |
| Research Curator | Portfolio-scoped context |
| Quant Forecaster | Kronos-style OHLCV forecasts per holding |
| Scenario Cartographer | MiroFish interviews / report / timeline |
| Compliance Skeptic | Concentration & assumption flags |
| Scenario Synthesizer | Base / upside / downside brief |
| Recommendation engine | Suggested moves → **human gate** |

## Roadmap

### Feature: Financial Terms Glossary
**Status:** Scoped, not yet built.

Every council run surfaces financial jargon — P/E ratio, EPS surprise, VIX, yield curve, basis points, etc. Non-expert investors shouldn't have to Google terms mid-decision.

**Planned implementation:**
- Add a `terms` field to the `CouncilRunState` output — a dict of `{term: plain_english_definition}` populated during each council run
- Research Curator scans research notes for known jargon and appends definitions automatically
- UI renders a collapsible glossary panel beneath the council brief
- Definitions are static (curated, no API cost) but tied to the specific terms used in that run — not a generic dictionary dump

**Why it matters:** Stock recommendations are only useful if the person reading them understands what's being said. This closes the literacy gap without requiring the user to leave the app.

---

### Feature: Compliance Web Search (Open Web Legal & Financial Scan)
**Status:** Scoped, not yet built.

The Compliance Skeptic currently flags hardcoded risks (concentration, Florida insurance, etc.). It has no awareness of:
- Recent regulatory actions against holdings (SEC enforcement, FTC investigations)
- Tax implications of suggested moves (wash sale rules, capital gains treatment)
- Sector-specific legal risks (AAPL App Store antitrust, etc.)
- Financial terms or concepts the council may not be accounting for

**Planned implementation:**
- Integrate a search API (Brave Search free tier or SerpAPI) as `src/apex_ledger/data/web_search.py`
- Add `SEARCH_API_KEY` to Settings
- Compliance Skeptic runs targeted searches per holding:
  - `"{symbol} SEC enforcement 2025"`
  - `"{symbol} regulatory risk {current_year}"`
  - `"tax implications selling {symbol} short term"`
- Results injected into `state.risk_flags` before the Recommendation Engine runs
- Caps at 3 searches per council run to stay within free tier limits

**Why it matters:** Keeps the council honest. A quant signal can look great on a stock that has a pending DOJ investigation — web search catches what structured data sources miss.

---



```bash
uv sync --extra curate
uv run --extra curate python scripts/curate_skillmd.py --limit 30
```

Dataset: [SkillMD-138K](https://huggingface.co/datasets/FayeZC/SkillMD-138K) (CC-BY-4.0 compilation; verify upstream license per skill before adoption).

## Tooling & ops

- [SETUP.md](SETUP.md) — full checklist (CLT, GitLab, MCP, MiroFish runtime, Docker)
- [GITLAB_SETUP.md](GITLAB_SETUP.md) — GitLab token / MCP details
- `.github/workflows/ci.yml` — pytest on push/PR to `main`
- `.devcontainer/` — VS Code / Cursor dev container (ports 5001 + 8080)

## Tests

```bash
uv sync --extra dev
uv run pytest tests/ -q
```
