# GitLab setup for Apex Ledger

## Token storage (do not commit)

Your GitLab PAT lives only in:

`~/.config/apex-ledger/env` (mode `600`)

`~/.zshrc` loads it:

```bash
[ -f "$HOME/.config/apex-ledger/env" ] && . "$HOME/.config/apex-ledger/env"
```

Never put tokens in this repo, `mcp.json`, or chat.

## MCP (Cursor)

Global `~/.cursor/mcp.json`:

| Server | Purpose |
|--------|---------|
| `git` | Local repo (`mcp-server-git` → `~/Projects/apex-ledger`) |
| `GitLab` | Official HTTP MCP (`https://gitlab.com/api/v4/mcp`) — OAuth if Duo enabled |
| `gitlab-pat` | PAT-based MCP via `${env:GITLAB_TOKEN}` |

**Restart Cursor** after changing the env file so MCP sees `GITLAB_TOKEN`.

## Git remote

| Remote | URL |
|--------|-----|
| `origin` | `https://gitlab.com/jeansgray/apex-ledger` |

**MiroFish** submodule stays on GitHub (`vendor/mirofish` → `666ghj/MiroFish`, AGPL).

## CLI

- `glab` — `~/.local/bin/glab`, authenticated via `GITLAB_TOKEN`
- Push/pull: `git push` / `git pull` on `main` (credential helper configured)

## Official GitLab MCP OAuth (optional)

If `GitLab` HTTP MCP shows “missing client ID”, use **`gitlab-pat`** instead, or complete OAuth in **Cursor → Settings → Tools & MCP → GitLab** (requires GitLab Duo + beta on Premium/Ultimate).
