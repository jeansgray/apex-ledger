---
name: apex-deps-audit
description: >-
  Audit Python dependency vulnerabilities (SCA) for Apex Ledger using pip-audit
  and lockfile review. Use before releases, after uv lock changes, or when
  dependabot-style updates land.
---

# Apex Dependencies Audit (SCA)

Software composition analysis for Apex Ledger Python dependencies (`pyproject.toml`, `uv.lock`).

## When to run

- After `uv lock` or dependency version bumps
- Weekly on active development branches
- Before Docker image rebuilds for collaborators

## Procedure

1. **Sync environment**

```bash
cd /path/to/apex-ledger
uv sync --extra dev
uv pip install pip-audit
```

2. **Run pip-audit**

```bash
uv run pip-audit
```

3. **Review lockfile drift**

```bash
git diff uv.lock pyproject.toml
```

4. **Docker base images** (manual)

Check `docker/Dockerfile.apex`, `Dockerfile.mirofish`, `Dockerfile.kronos` for pinned base image tags; rebuild after CVE advisories.

5. **Vendor submodule**

`vendor/mirofish` has its own dependency tree. Run audit inside that tree separately if MiroFish is updated — do not mix into Apex proprietary SBOM without license review.

## Remediation priority

| Priority | Action |
|----------|--------|
| Critical / High | Bump dependency or pin patched version; re-run tests |
| Medium | Schedule upgrade; document accepted risk if blocked |
| Low | Track in backlog |

## Output format

```markdown
## SCA summary
- **pip-audit:** N vulnerabilities (X critical, Y high)
- **Lockfile:** changed / unchanged

## Vulnerabilities
| Package | Version | CVE | Fix version | Status |
|---------|---------|-----|-------------|--------|

## Verdict
- [ ] Clean
- [ ] Upgrade required before release
```

After upgrades: `uv run pytest tests/ -q` and rebuild Docker stack.
