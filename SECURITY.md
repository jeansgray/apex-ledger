# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

**Do not open a public GitHub or GitLab issue for exploitable security bugs.**

Report vulnerabilities privately using one of:

1. **GitHub Security Advisories** (preferred):  
   https://github.com/jeansgray/apex-ledger/security/advisories/new
2. **GitLab confidential issue** (if you only have GitLab access):  
   https://gitlab.com/jeansgray/apex-ledger/-/issues/new?issue[confidential]=true

Include:

- Description and impact
- Steps to reproduce
- Affected paths or endpoints
- Suggested fix (optional)

We aim to acknowledge reports within **3 business days** and share a remediation timeline when confirmed.

## Scope

**In scope**

- `src/apex_ledger/` — FastAPI app, council, ledger, integrations (Plaid/Schwab OAuth)
- Docker Compose deployment (`docker-compose.yml`, `docker/`)
- GitHub Actions workflows (`.github/workflows/`)
- Collaborator docs site (`docs/`)

**Out of scope**

- `vendor/mirofish/` (AGPL submodule — report upstream separately)
- User-managed secrets in local `.env` or `data/integrations.json`
- Third-party APIs (Plaid, Schwab, OpenAI, Zep, Alpha Vantage)

## Security Practices (contributors)

- **Never commit secrets.** Use `.env` (gitignored) and `python3 scripts/configure_keys.py` for MiroFish keys.
- **OAuth tokens** live in `data/integrations.json` (gitignored) — not in source control.
- **AGPL boundary:** Apex talks to MiroFish over HTTP only; do not import `vendor/mirofish` Python modules into proprietary code.
- **Human approval gates** — reconciliation and investment moves require explicit user approval before posting.
- Run security checks before merging: see `.cursor/skills/apex-sast-check`, `apex-dast-check`, `apex-deps-audit`, and `apex-secrets-scan`.

## Automated Checks

CI runs unit tests on every PR. Security scanning skills document optional SAST/SCA/DAST steps for local and pre-release review.
