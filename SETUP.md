# Apex Ledger — setup checklist

Use this when onboarding a new machine or a collaborator.

## 1. Clone the repo

```bash
git clone --recurse-submodules https://gitlab.com/jeansgray/apex-ledger.git
cd apex-ledger
```

If you already cloned without submodules:

```bash
git submodule update --init --recursive
```

## 2. System prerequisites

| Requirement | Check |
|-------------|--------|
| Git + Xcode CLT (macOS) | `git --version` |
| **uv** | `uv --version` — install from https://docs.astral.sh/uv/ |
| Python **3.11+** (Apex) | `uv python install 3.11` |
| Python **3.12** (MiroFish) | `uv python install 3.12` |
| Node **18+** (MiroFish tooling) | `node -v` |

Add local bins to PATH in `~/.zshrc` if needed:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

## 3. API keys (live MiroFish simulations)

**Required for live sims only.** Demo fixture mode works without them.

| Key | Sign up | Env var |
|-----|---------|---------|
| OpenAI (or OpenAI-compatible LLM) | https://platform.openai.com/api-keys | `LLM_API_KEY` |
| Zep Cloud | https://app.getzep.com/ | `ZEP_API_KEY` |

Setup:

```bash
cp .env.example .env
# Edit .env — paste keys (never commit this file)
python3 scripts/configure_keys.py
```

This writes:

- `~/.config/apex-ledger/mirofish.env` (chmod 600)
- `vendor/mirofish/.env` (copy for the backend process)

Verify from Apex:

```bash
curl -s http://127.0.0.1:8080/health | python3 -m json.tool
# "keys": { "valid": true, ... }
```

**Security:** Do not paste keys in chat, issues, or MRs. Rotate any key that was exposed.

## 4. Run services

**Terminal 1 — MiroFish** (port 5001):

```bash
uv sync
python3 scripts/setup_mirofish.py
UV_PYTHON=$(uv python find 3.12) uv run --directory vendor/mirofish/backend python run.py
```

**Terminal 2 — Apex Ledger** (port 8080):

```bash
uv sync --extra dev
uv run apex-ledger serve --port 8080
```

Open http://127.0.0.1:8080

## 5. Cursor MCP (contributors)

For GitLab issues, MRs, and CI from Cursor:

1. Install/enable the **GitLab** plugin in Cursor.
2. **Settings → Tools & MCP → GitLab** — OAuth login **or** PAT via env (`GITLAB_TOKEN`).
3. Optional: **Git** MCP for local repo operations.
4. **Restart Cursor** after MCP changes.

See [GITLAB_SETUP.md](GITLAB_SETUP.md) for PAT vs OAuth and `~/.cursor/mcp.json` examples.

GitLab CLI (optional):

```bash
glab auth login --web
glab auth status
```

## 6. GitLab remote

- **HTTPS:** `https://gitlab.com/jeansgray/apex-ledger.git`
- **SSH:** `git@gitlab.com:jeansgray/apex-ledger.git`

Push after auth:

```bash
git push -u origin main
```

## 7. MiroFish submodule

`vendor/mirofish` is an AGPL submodule — HTTP boundary only; do not import it from `src/apex_ledger/`.

Refresh:

```bash
git submodule update --init --recursive
```

Seeded read-only fixture (no live keys): `sim_apex_personal_investor`

Optional one-shot live bootstrap (long-running):

```bash
python3 scripts/bootstrap_personal_investor_simulation.py
```

## 8. What's not wired yet

- Real personal holdings / profile (demo ledger is seeded)
- Production deployment / auth

Track progress in GitLab issues on the project board.
