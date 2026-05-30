#!/usr/bin/env python3
"""Seed a completed personal-investor MiroFish simulation fixture (read-only APIs)."""

from __future__ import annotations

import argparse
import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path

SIMULATION_ID = "sim_apex_personal_investor"
PROJECT_ID = "proj_apex_personal_investor"
GRAPH_ID = "mirofish_apex_personal_investor"
REPORT_ID = "report_apex_personal_investor"
REQUIREMENT = (
    "Simulate how retail investors react if the Fed cuts rates by 50bps while "
    "inflation stays sticky. Focus on ETF-heavy portfolios (VTI, BND mix)."
)

ROOT = Path(__file__).resolve().parents[1]
NOW = datetime.now(timezone.utc).isoformat()


def _uploads_root() -> Path:
    return Path(os.environ.get("MIROFISH_UPLOADS", ROOT / "vendor/mirofish/backend/uploads"))


def _insights_root() -> Path:
    return Path(os.environ.get("APEX_INSIGHTS_DIR", ROOT / "data/mirofish_insights"))


def main() -> str:
    parser = argparse.ArgumentParser(description="Seed personal-investor MiroFish demo fixture")
    parser.add_argument("--skip-uploads", action="store_true", help="Only write local insights JSON")
    parser.add_argument("--skip-insights", action="store_true", help="Only write MiroFish uploads tree")
    args = parser.parse_args()

    mirofish_uploads = _uploads_root()
    if not args.skip_uploads:
        _seed_uploads(mirofish_uploads)

    if not args.skip_insights:
        _seed_insights(_insights_root())

    print(SIMULATION_ID)
    return SIMULATION_ID


def _seed_uploads(mirofish_uploads: Path) -> None:
    sim_dir = mirofish_uploads / "simulations" / SIMULATION_ID
    sim_dir.mkdir(parents=True, exist_ok=True)

    state = {
        "simulation_id": SIMULATION_ID,
        "project_id": PROJECT_ID,
        "graph_id": GRAPH_ID,
        "enable_twitter": True,
        "enable_reddit": True,
        "status": "completed",
        "entities_count": 3,
        "profiles_count": 3,
        "entity_types": ["RetailInvestor", "FinancialCommentator", "PolicyWatcher"],
        "config_generated": True,
        "config_reasoning": "Seeded fixture for Apex Ledger personal investor council.",
        "current_round": 5,
        "twitter_status": "completed",
        "reddit_status": "completed",
        "created_at": NOW,
        "updated_at": NOW,
        "error": None,
    }
    (sim_dir / "state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")

    profiles = [
        {
            "agent_id": 0,
            "name": "ETF_Retail_Investor",
            "bio": "40yo investor with VTI/BND blend, rate-sensitive.",
        },
        {
            "agent_id": 1,
            "name": "Macro_Commentator",
            "bio": "Tracks Fed policy and sticky inflation narratives.",
        },
        {
            "agent_id": 2,
            "name": "Risk_Aware_Saver",
            "bio": "Prefers cash and short duration when real yields fall.",
        },
    ]
    (sim_dir / "reddit_profiles.json").write_text(json.dumps(profiles, indent=2), encoding="utf-8")

    with (sim_dir / "twitter_profiles.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["user_id", "name", "username", "description"])
        writer.writeheader()
        for p in profiles:
            writer.writerow(
                {
                    "user_id": p["agent_id"],
                    "name": p["name"],
                    "username": p["name"].lower(),
                    "description": p["bio"],
                }
            )

    (sim_dir / "simulation_config.json").write_text(
        json.dumps(
            {
                "simulation_requirement": REQUIREMENT,
                "max_rounds": 5,
                "platforms": ["twitter", "reddit"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    twitter_dir = sim_dir / "twitter"
    twitter_dir.mkdir(exist_ok=True)
    actions = [
        {
            "round_num": 1,
            "timestamp": NOW,
            "platform": "twitter",
            "agent_id": 0,
            "agent_name": "ETF_Retail_Investor",
            "action_type": "CREATE_POST",
            "action_args": {"content": "Rate cut helps duration but sticky CPI keeps me cautious on long bonds."},
            "result": "posted",
            "success": True,
        },
        {
            "round_num": 2,
            "timestamp": NOW,
            "platform": "twitter",
            "agent_id": 1,
            "agent_name": "Macro_Commentator",
            "action_type": "CREATE_POST",
            "action_args": {"content": "Equity risk premium may compress if cuts arrive before inflation truly cools."},
            "result": "posted",
            "success": True,
        },
        {
            "round_num": 3,
            "timestamp": NOW,
            "platform": "twitter",
            "agent_id": 2,
            "agent_name": "Risk_Aware_Saver",
            "action_type": "CREATE_POST",
            "action_args": {"content": "I'd trim equity beta and keep dry powder until real yields stabilize."},
            "result": "posted",
            "success": True,
        },
    ]
    with (twitter_dir / "actions.jsonl").open("w", encoding="utf-8") as f:
        for action in actions:
            f.write(json.dumps(action, ensure_ascii=False) + "\n")

    project_dir = mirofish_uploads / "projects" / PROJECT_ID
    project_dir.mkdir(parents=True, exist_ok=True)
    project = {
        "project_id": PROJECT_ID,
        "name": "Apex Personal Investor — Rate Cut Scenario",
        "status": "graph_completed",
        "created_at": NOW,
        "updated_at": NOW,
        "files": [{"filename": "investor_brief.md", "size": 1200}],
        "total_text_length": 1200,
        "ontology": {
            "entity_types": ["RetailInvestor", "FinancialCommentator", "PolicyWatcher"],
            "edge_types": ["reacts_to", "influences"],
            "analysis_summary": "Personal investor reaction network for macro rate scenarios.",
        },
        "analysis_summary": "Personal investor reaction network for macro rate scenarios.",
        "graph_id": GRAPH_ID,
        "graph_build_task_id": None,
        "simulation_requirement": REQUIREMENT,
        "chunk_size": 500,
        "chunk_overlap": 50,
        "error": None,
    }
    (project_dir / "project.json").write_text(json.dumps(project, indent=2), encoding="utf-8")
    (project_dir / "extracted_text.txt").write_text(
        "# Personal investor brief\n\n"
        "Portfolio: 60/40 ETF mix (VTI/BND). Question: Fed cuts 50bps, inflation sticky.\n",
        encoding="utf-8",
    )

    report_dir = mirofish_uploads / "reports" / REPORT_ID
    report_dir.mkdir(parents=True, exist_ok=True)
    summary = (
        "Retail personas split: equity holders see near-term relief, bond holders fear "
        "inflation surprise, savers stay defensive until real yields clarify."
    )
    markdown = (
        f"# Personal Investor Scenario Report\n\n{summary}\n\n"
        "## Base case\nRate cut supports equities modestly; bond rally capped by sticky CPI.\n\n"
        "## Upside case\nSoft landing narrative boosts VTI-style beta.\n\n"
        "## Downside case\nInflation re-acceleration triggers duration selloff in BND.\n"
    )
    meta = {
        "report_id": REPORT_ID,
        "simulation_id": SIMULATION_ID,
        "graph_id": GRAPH_ID,
        "simulation_requirement": REQUIREMENT,
        "status": "completed",
        "outline": {
            "title": "Rate Cut Scenario — Personal Investors",
            "summary": summary,
            "sections": [
                {"title": "Base case", "content": "Moderate equity support, limited bond upside."},
                {"title": "Upside case", "content": "Risk assets rally on soft-landing narrative."},
                {"title": "Downside case", "content": "Inflation shock hurts duration-heavy portfolios."},
            ],
        },
        "markdown_content": markdown,
        "created_at": NOW,
        "completed_at": NOW,
        "error": None,
    }
    (report_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    (report_dir / "full_report.md").write_text(markdown, encoding="utf-8")


def _seed_insights(insights: Path) -> None:
    insights.mkdir(parents=True, exist_ok=True)
    (insights / f"{SIMULATION_ID}.json").write_text(
        json.dumps(
            {
                "simulation_id": SIMULATION_ID,
                "insights": [
                    "ETF investor: rate cut helps equity beta but BND upside is limited if CPI stays hot.",
                    "Macro commentator: watch for equity risk premium compression into cuts.",
                    "Risk-aware saver: keep dry powder until real yields stabilize.",
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
