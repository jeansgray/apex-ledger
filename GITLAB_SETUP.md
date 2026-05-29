# GitLab setup for Apex Ledger (fix “missing client ID”)

## What “missing client ID” means

Cursor is trying to **log in to GitLab with OAuth**. Some flows expect a **Client ID** from a GitLab “Application” (OAuth app).  

The **official GitLab MCP** (`https://gitlab.com/api/v4/mcp`) is supposed to use **Dynamic Client Registration** (no manual Client ID). If you still see “missing client ID”, Cursor’s OAuth handshake did not finish—often because Duo/beta is off, the browser step was skipped, or a duplicate/broken MCP entry exists.

**MiroFish** stays on GitHub as a submodule (`vendor/mirofish` → `github.com/666ghj/MiroFish`). Only **apex-ledger** uses GitLab.

---

## Choose one path (recommended: Path B first)

### Path A — Official GitLab MCP + OAuth (plugin default)

**Requirements (GitLab.com):**

- GitLab **Premium or Ultimate** on your top-level group  
- **GitLab Duo** enabled  
- **Beta / experimental features** enabled for that group  

**In Cursor (no terminal):**

1. **Cursor → Settings → Cursor Settings → Tools & MCP**
2. Under **Installed MCP Servers**, find **GitLab**
3. If it shows an error, toggle it **off**, then **on** again (or remove duplicate “GitLab” entries if you see two)
4. **Quit Cursor completely** and reopen
5. When the browser opens, **Approve** access to GitLab.com  
6. In chat, you can type **`mcp_auth`** if the browser did not open

You should **not** need to paste a Client ID for the official server when Dynamic Client Registration works.

**If you must use a manual OAuth app** (only if Cursor/support asks for Client ID + Secret):

| Field | Value |
|--------|--------|
| **GitLab** | User menu → **Edit profile** → **Applications** → **Add new application** |
| **Name** | `Cursor Apex Ledger` |
| **Redirect URI** | `cursor://anysphere.cursor-mcp/oauth/callback` |
| **Confidential** | No (unless Cursor requires secret) |
| **Scopes** | `api`, `read_user`, `read_repository`, `write_repository` |

Copy **Application ID** (Client ID) and **Secret** only into **Cursor’s GitLab MCP OAuth fields** in Settings (not into this repo). Do not commit secrets.

---

### Path B — Personal Access Token (PAT) — no Client ID (recommended)

Works without OAuth Client ID. Uses the **`gitlab-pat`** MCP server in `~/.cursor/mcp.json`.

**On GitLab.com (browser):**

1. Open **Avatar → Edit profile → Personal access tokens**  
   (or go to `https://gitlab.com/-/user_settings/personal_access_tokens`)
2. **Add new token**
3. **Name:** `cursor-apex-ledger`
4. **Scopes:** enable at least  
   - `api`  
   - `read_repository`  
   - `write_repository`  
   - `read_user` (optional but useful)
5. **Create token** → copy the token once (`glpat-…`)

**In Cursor (no terminal):**

1. **Cursor → Settings → Cursor Settings → General** (or **Secrets** / env, depending on your Cursor version)  
   Add environment variable: **`GITLAB_TOKEN`** = your `glpat-…` token  
   *Or* add the same line to your Mac login environment so Cursor inherits it when launched from Dock.
2. **Restart Cursor**
3. **Tools & MCP** → confirm **`gitlab-pat`** is connected (green)

The agent can then use **`glab`** for push/pull once `GITLAB_TOKEN` is visible to the shell Cursor uses.

---

## Repo remote (already set)

| Remote | URL |
|--------|-----|
| `origin` | `https://gitlab.com/jeansgray/apex-ledger.git` |

**If the project does not exist yet on GitLab:**  
**GitLab → New project → Create blank project → Project name:** `apex-ledger` → **Create project** (do not initialize with README if this machine already has commits).

---

## After auth works

- Push happens automatically when `GITLAB_TOKEN` is set and `glab`/git credentials work.  
- **Restart Cursor** after any MCP or token change.  
- Git MCP (`mcp-server-git`) still points at `~/Projects/apex-ledger` for local history/diffs.

---

## Quick reference

| Item | Location |
|------|-----------|
| Global MCP | `~/.cursor/mcp.json` |
| Project MCP | `.cursor/mcp.json` (GitLab HTTP only) |
| This guide | `GITLAB_SETUP.md` |
| `glab` CLI | `~/.local/bin/glab` |
| GitHub MCP | **Removed** (was `GITHUB_TOKEN` / `@modelcontextprotocol/server-github`) |
