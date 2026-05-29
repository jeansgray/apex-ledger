# Apex Ledger

Finance and investment platform built around scenario simulation (MiroFish) and ledger/portfolio features.

## Repository layout (Option B)

| Path | Purpose |
|------|---------|
| `vendor/mirofish/` | Git submodule — upstream [MiroFish](https://github.com/666ghj/MiroFish) (AGPL-3.0) |
| (your code) | Proprietary Apex Ledger application — use a license you choose |

After Xcode Command Line Tools and `gh auth login` are set up:

```bash
export PATH="$HOME/.local/bin:$PATH"
cd ~/Projects/apex-ledger
git submodule update --init --recursive
```

## Tooling

- `gh` — GitHub CLI (`~/.local/bin/gh`)
- `uv` / `uvx` — Python tools + Git MCP (`~/.local/bin/uv`)
- Node/npx — GitHub MCP (`~/.local/bin/node`)

Add to shell: `source ~/.local/bin/env.sh`

## MCP (Cursor)

Global config: `~/.cursor/mcp.json` (Git + GitHub servers). Set `GITHUB_TOKEN` in your environment, then restart Cursor.
