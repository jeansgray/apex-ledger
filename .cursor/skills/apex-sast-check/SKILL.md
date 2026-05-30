---
name: apex-sast-check
description: >-
  Run static application security testing (SAST) on Apex Ledger Python code.
  Use before releases, after auth/integration changes, or when reviewing PRs
  that touch API routes, OAuth, or ledger storage.
---

# Apex SAST Check

Static analysis for **Apex Ledger** (`src/apex_ledger/`). Do not scan `vendor/mirofish/` as part of proprietary SAST — treat it as a separate AGPL service boundary.

## When to run

- PRs touching `src/apex_ledger/api/`, `integrations/`, `ledger/`, or `config.py`
- Before enabling Plaid/Schwab OAuth in production
- After adding new endpoints or file upload handlers

## Procedure

1. **Install dev tools**

```bash
cd /path/to/apex-ledger
uv sync --extra dev
uv pip install bandit
```

2. **Ruff lint** (style + some bug patterns)

```bash
uv run ruff check src/apex_ledger tests
```

3. **Bandit** (Python SAST)

```bash
uv run bandit -r src/apex_ledger -ll -x tests
```

4. **Manual review hotspots**

| Area | Check |
|------|-------|
| `api/app.py` | OAuth callbacks, token exchange, no secrets in responses |
| `integrations/` | Tokens stored only in `data/integrations.json`; validate redirect URIs |
| `ledger/store.py` | Parameterized SQL only; no string-concatenated queries |
| `config.py` | Secrets loaded from env, not hardcoded |
| `web/index.html` | No API keys in client JS; OAuth flows use server-side exchange |

5. **CSV / file upload**

- Confirm upload size limits and path traversal are blocked
- Parsed CSV must not execute code or write outside `data/`

## Output format

```markdown
## SAST summary
- **Ruff:** pass / N issues (list critical)
- **Bandit:** pass / N findings (severity + file:line)
- **Manual review:** pass / concerns

## Findings
| Severity | File | Issue | Recommendation |
|----------|------|-------|----------------|
| high/medium/low | ... | ... | ... |

## Verdict
- [ ] Safe to merge
- [ ] Merge with follow-up issues filed
- [ ] Block until fixed
```

File GitHub/GitLab issues for **high** and **medium** findings before merge.
