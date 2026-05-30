# Apex Ledger

Personal investor platform: **MiroFish-backed scenario council** + **ledger reconciliation**, with Robinhood-style **suggested moves** and human approval gates.

Built for a single investor (holdings, cash goals, life questions) — not a generic trading bot.

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

**Demo mode** works without keys (seeded fixture `sim_apex_personal_investor`). **Live MiroFish simulations** need two keys:

| Variable | Where to get it | Used for |
|----------|-----------------|----------|
| `LLM_API_KEY` | [OpenAI API keys](https://platform.openai.com/api-keys) (`sk-...`) | MiroFish agents + ontology (OpenAI-compatible) |
| `ZEP_API_KEY` | [Zep Cloud](https://app.getzep.com/) (free tier OK) | MiroFish knowledge graph / memory |

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

## Docker (repeatable collaborator path)

Install [Docker Desktop for Mac](https://docs.docker.com/desktop/setup/install/mac-install/) (or Linux/Windows equivalents), then from the repo root:

```bash
git submodule update --init --recursive
cp .env.example .env
# optional: add LLM_API_KEY / ZEP_API_KEY, then python3 scripts/configure_keys.py
docker compose up --build
```

- Apex UI: http://127.0.0.1:8080  
- MiroFish: http://127.0.0.1:5001  

Secrets load from mounted `.env` only — never bake keys into images. See [SETUP.md](SETUP.md) for details.

## Quick start (uv, local)

```bash
cd ~/Projects/apex-ledger
git submodule update --init --recursive
cp .env.example .env

# Optional but recommended for live sims — add keys to .env, then:
python3 scripts/configure_keys.py

# 1) MiroFish backend (terminal 1)
uv sync
python3 scripts/setup_mirofish.py
UV_PYTHON=$(uv python find 3.12) uv run --directory vendor/mirofish/backend python run.py
# → http://127.0.0.1:5001

# 2) Apex Ledger (terminal 2)
uv sync --extra dev
uv run apex-ledger serve --port 8080
# → http://127.0.0.1:8080
```

CLI smoke test:

```bash
uv run apex-ledger council-run "How would a Fed rate cut affect my ETF-heavy portfolio?"
```

### What to expect in the UI

- **Suggested moves** — simulation-informed buy/hold/trim ideas (approve to save; nothing trades automatically).
- **Live simulation** — first question on a topic may spawn a background MiroFish run (often 5–15 min); UI polls until ready.
- **Demo mode** — if keys are missing, uses fixture `sim_apex_personal_investor`.
- **Personal data** — demo ledger is seeded; real holdings/profile wiring is planned next.

## Apex Council (personal investor)

| Role | Lane |
|------|------|
| Ledger Steward | Holdings + unmatched transactions |
| Reconciliation Proposer | Category proposals → **human gate** |
| Research Curator | Portfolio-scoped context |
| Scenario Cartographer | MiroFish interviews / report / timeline |
| Compliance Skeptic | Concentration & assumption flags |
| Scenario Synthesizer | Base / upside / downside brief |
| Recommendation engine | Suggested moves → **human gate** |

## SkillMD curation

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
