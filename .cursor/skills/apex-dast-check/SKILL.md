---
name: apex-dast-check
description: >-
  Run dynamic application security testing (DAST) against a running Apex Ledger
  stack. Use after docker compose up, before exposing :8080 beyond localhost,
  or when validating OAuth and integration endpoints.
---

# Apex DAST Check

Dynamic tests against the **running stack** (Apex `:8080`, MiroFish `:5001`, Kronos `:5002`). Requires `docker compose up` or equivalent.

## When to run

- Before sharing the dashboard on a non-local network
- After OAuth route changes (Plaid Link, Schwab callback)
- Before collaborator production-like deployments

## Prerequisites

```bash
export PATH="$HOME/Applications/Docker.app/Contents/Resources/bin:$PATH"
cd /path/to/apex-ledger
docker compose up -d
curl -sf http://127.0.0.1:8080/health
```

## Procedure

1. **Health and info disclosure**

```bash
curl -s http://127.0.0.1:8080/health | python3 -m json.tool
curl -s http://127.0.0.1:8080/config | python3 -m json.tool
```

Confirm `/config` does **not** expose API keys, tokens, or integration secrets.

2. **Unauthenticated access**

Probe sensitive routes without auth (Apex has no login today — everything on `:8080` is local-trust):

| Endpoint | Expected |
|----------|----------|
| `GET /ledger/detail` | Returns local ledger (OK on localhost only) |
| `POST /council/run` | Runs analysis (OK on localhost only) |
| `DELETE /integrations/plaid` | Should not crash; verify idempotent |
| `GET /oauth/schwab/callback?code=fake` | Graceful error, no token leak |

**Finding:** Apex is designed for **single-user localhost**. Flag if bound to `0.0.0.0` on a public host without a reverse proxy and auth.

3. **OAuth callback validation**

- Schwab callback must reject missing/invalid `code` without exposing stack traces
- Plaid exchange must reject empty `public_token`

4. **Injection probes** (non-destructive)

```bash
curl -s -X POST http://127.0.0.1:8080/council/run \
  -H 'Content-Type: application/json' \
  -d '{"question":"<script>alert(1)</script> test","seed_demo":false}'
```

Confirm response JSON/HTML does not reflect raw script tags unescaped in the UI.

5. **MiroFish / Kronos boundaries**

```bash
curl -sf http://127.0.0.1:5001/health
curl -sf http://127.0.0.1:5002/health
```

These services should not be exposed publicly in production without network isolation.

6. **Optional tooling**

If installed, run OWASP ZAP or `nuclei` against `http://127.0.0.1:8080` with **passive** scan only on localhost.

## Output format

```markdown
## DAST summary
- **Target:** http://127.0.0.1:8080 (stack version / commit)
- **Exposure model:** localhost single-user / other

## Tests
| Test | Result | Notes |
|------|--------|-------|
| Config leak | pass/fail | |
| OAuth error handling | pass/fail | |
| XSS reflection | pass/fail | |

## Verdict
- [ ] OK for local dev
- [ ] Not safe for public exposure without auth + TLS
```

Report **high** issues via `SECURITY.md` private disclosure if they affect deployed instances.
