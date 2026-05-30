---
name: apex-secrets-scan
description: >-
  Scan Apex Ledger for accidentally committed secrets, API keys, and tokens.
  Use before every push, after editing .env.example, or when reviewing partner PRs.
---

# Apex Secrets Scan

Detect leaked credentials in git history and working tree. Complements SAST — focused on **secret exposure**, not code logic.

## When to run

- Before `git push`
- When reviewing PRs that touch `.env.example`, scripts, or docs
- After any paste of API keys into chat or files

## Procedure

1. **Gitignore sanity**

Confirm these are in `.gitignore` and never staged:

- `.env`
- `data/integrations.json`
- `data/ledger.db`
- `~/.config/apex-ledger/` (outside repo)

```bash
git check-ignore -v .env data/integrations.json || echo "WARN: not ignored"
git status
```

2. **Pattern grep** (working tree)

```bash
cd /path/to/apex-ledger
rg -n "(sk-[A-Za-z0-9]{20,}|z_[A-Za-z0-9._-]{20,}|PLAID_SECRET=\\S+|SCHWAB_APP_SECRET=\\S+)" \
  --glob '!.env' --glob '!uv.lock' --glob '!**/__pycache__/**'
```

3. **Optional: gitleaks**

```bash
# if installed: brew install gitleaks
gitleaks detect --source . --verbose --redact
```

4. **`.env.example` review**

Placeholders only — no real keys:

```bash
rg "=sk-|z_1dWlk" .env.example && echo "FAIL: real-looking secret in example"
```

5. **Docs and SITREP**

Scan `docs/`, `SITREP.md`, `README.md` for pasted credentials.

## If secrets are found

1. **Rotate** the exposed key immediately (OpenAI, Zep, Plaid, Schwab, Alpha Vantage)
2. Remove from files; `git commit` the fix
3. If pushed to remote: consider `git filter-repo` or BFG for history rewrite (coordinate with partner)
4. Report internally via `SECURITY.md` if production tokens were exposed

## Output format

```markdown
## Secrets scan
- **Working tree:** clean / N findings
- **Staged files:** clean / N findings
- **.env.example:** placeholders only — yes/no

## Findings
| File | Line | Type | Action |
|------|------|------|--------|

## Verdict
- [ ] Safe to push
- [ ] Rotate keys and scrub before push
```
