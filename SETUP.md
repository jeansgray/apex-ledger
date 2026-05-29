# Apex Ledger — setup checklist

## 1. Xcode Command Line Tools (required for `git`)

macOS `/usr/bin/git` is a stub until this is installed.

**In Terminal (GUI session):**

```bash
xcode-select --install
```

Click **Install** in the dialog, wait until finished, then verify:

```bash
git --version
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

## 3. GitHub CLI login

```bash
gh auth login
```

Choose: GitHub.com → HTTPS → Login with browser (or token).

Verify:

```bash
gh auth status
gh repo view jeansgray/apex-ledger
```

If the repo is **private**, ensure your account can access it.

## 4. Connect this folder to `apex-ledger` on GitHub

From `~/Projects/apex-ledger` (after git works):

**If the GitHub repo already has commits:**

```bash
cd ~/Projects/apex-ledger
git clone https://github.com/jeansgray/apex-ledger.git /tmp/apex-remote
# merge remote history, or replace local with clone — pick one workflow with your team
```

**If the GitHub repo is empty and this folder is the source of truth:**

```bash
cd ~/Projects/apex-ledger
git init
git remote add origin https://github.com/jeansgray/apex-ledger.git
git add .
git commit -m "Initial Apex Ledger layout with MiroFish vendor (Option B)"
git branch -M main
git push -u origin main
```

## 5. Add MiroFish as a real submodule (recommended)

The zip fallback extraction failed in this environment, so `vendor/mirofish` is not populated yet. After `git` works:

```bash
cd ~/Projects/apex-ledger
rm -rf vendor/mirofish
git submodule add https://github.com/666ghj/MiroFish.git vendor/mirofish
git submodule update --init --recursive
git commit -m "Track MiroFish as submodule (AGPL upstream)"
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
