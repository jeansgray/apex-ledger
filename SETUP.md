# Apex Ledger — setup checklist

## 1. Xcode Command Line Tools (required for `git`)

**Status:** Installed (`/Library/Developer/CommandLineTools`). Verify anytime:

```bash
git --version
xcode-select -p
```

If `git` fails again, run `xcode-select --install` or:

```bash
sudo softwareupdate --install "Command Line Tools for Xcode 26.5-26.5" --verbose
```

## 2. Shell PATH

Add to `~/.zshrc` (create the file if needed):

```bash
source ~/.local/bin/env.sh
```

Open a new terminal tab, then:

```bash
which gh uv node npx
```

## 3. GitLab (primary remote)

- **Remote:** `https://gitlab.com/jeansgray/apex-ledger.git` (or SSH `git@gitlab.com:jeansgray/apex-ledger.git`)
- **CLI:** `glab` in `~/.local/bin` — run `glab auth login --web` or approve OAuth in Cursor (**Settings → Tools & MCP → GitLab**).
- **MCP:** GitLab plugin uses HTTP `https://gitlab.com/api/v4/mcp` (OAuth via Cursor; no `GITHUB_TOKEN`).

Create the project on GitLab first if it does not exist: **New project → Create blank project → name `apex-ledger`**.

## 4. Push to GitLab

After `glab auth status` shows a valid token:

```bash
cd ~/Projects/apex-ledger
git push -u origin main
```

Or: `glab repo create jeansgray/apex-ledger --private` then push.

## 5. MiroFish submodule

**Status:** `vendor/mirofish` is added and initialized (commit `1f7bba0` on `main`).

To refresh later:

```bash
cd ~/Projects/apex-ledger
git submodule update --init --recursive
```

## 6. GitHub token for MCP

Create a fine-grained or classic PAT at https://github.com/settings/tokens with `repo` scope (for private repos).

```bash
echo 'export GITHUB_TOKEN="ghp_..."' >> ~/.zshrc
source ~/.zshrc
```

Restart **Cursor** so `~/.cursor/mcp.json` loads Git + GitHub MCP servers.

## 7. MiroFish runtime (when you run simulations)

- Node 18+ (installed at `~/.local/bin/node`)
- Python 3.11–3.12 + `uv` (installed)
- Copy `vendor/mirofish/.env.example` → `vendor/mirofish/.env` and add LLM + Zep keys
