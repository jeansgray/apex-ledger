#!/usr/bin/env python3
"""Filter SkillMD-138K for finance skills and emit a review manifest.

Requires: uv sync --extra curate
Dataset: https://huggingface.co/datasets/FayeZC/SkillMD-138K (CC-BY-4.0 compilation;
individual skills retain upstream licenses — review before adoption).

Usage:
  uv run --extra curate python scripts/curate_skillmd.py --limit 50
  uv run --extra curate python scripts/curate_skillmd.py --write-manifest
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

FINANCE_KEYWORDS = re.compile(
    r"\b("
    r"finance|financial|portfolio|ledger|reconcil|invest|stock|equity|"
    r"dividend|cash.?flow|balance.?sheet|sec.?filing|10-?k|10-?q|"
    r"risk|budget|expense|transaction|brokerage|tax.?loss"
    r")\b",
    re.I,
)

ROLE_HINTS: dict[str, re.Pattern[str]] = {
    "ledger_steward": re.compile(r"ledger|reconcil|transaction|bookkeep|expense", re.I),
    "scenario_cartographer": re.compile(r"scenario|forecast|simulation|what.?if", re.I),
    "research_curator": re.compile(r"news|filing|sec|research|sentiment", re.I),
    "compliance_skeptic": re.compile(r"risk|compliance|concentration|drawdown", re.I),
}


def score_row(content: str, repo: str, stars: int) -> tuple[int, list[str]]:
    score = 0
    roles: list[str] = []
    if FINANCE_KEYWORDS.search(content):
        score += 3
    if FINANCE_KEYWORDS.search(repo):
        score += 1
    score += min(stars // 500, 5)
    for role, pattern in ROLE_HINTS.items():
        if pattern.search(content) or pattern.search(repo):
            roles.append(role)
            score += 1
    return score, roles


def main() -> None:
    parser = argparse.ArgumentParser(description="Curate finance skills from SkillMD-138K")
    parser.add_argument("--limit", type=int, default=30, help="Max candidates to print")
    parser.add_argument(
        "--write-manifest",
        action="store_true",
        help="Write top candidates to skills/manifest.candidates.json (not auto-imported)",
    )
    parser.add_argument(
        "--min-score",
        type=int,
        default=4,
        help="Minimum relevance score",
    )
    args = parser.parse_args()

    from datasets import load_dataset

    ds = load_dataset("FayeZC/SkillMD-138K", split="train")
    candidates: list[dict] = []

    for row in ds:
        content = row["content"]
        score, roles = score_row(content, row["repo"], int(row["stars"]))
        if score < args.min_score:
            continue
        candidates.append(
            {
                "score": score,
                "roles": roles,
                "name": _extract_name(content) or Path(row["path"]).stem,
                "repo": row["repo"],
                "path": row["path"],
                "html_url": row["html_url"],
                "content_hash": row["content_hash"],
                "stars": row["stars"],
                "license_note": "Verify upstream repo license before copying content",
            }
        )

    candidates.sort(key=lambda x: (-x["score"], -x["stars"]))
    top = candidates[: args.limit]

    print(f"Found {len(candidates)} candidates (showing {len(top)})")
    for item in top:
        roles = ", ".join(item["roles"]) or "unassigned"
        print(
            f"[{item['score']}] {item['name']} ({roles}) — "
            f"{item['repo']} — {item['html_url']}"
        )

    if args.write_manifest:
        out = Path("skills/manifest.candidates.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"candidates": top}, indent=2), encoding="utf-8")
        print(f"Wrote {out}")


def _extract_name(content: str) -> str | None:
    for line in content.splitlines()[:20]:
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip().strip('"').strip("'")
    return None


if __name__ == "__main__":
    main()
