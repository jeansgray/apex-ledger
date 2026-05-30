#!/usr/bin/env python3
"""Run a live personal-investor simulation through MiroFish APIs (requires real keys)."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
BRIEF = ROOT / "data" / "investor_brief.md"
BASE = "http://127.0.0.1:5001"
POLL_SECONDS = 5
MAX_WAIT = 3600


def wait_until(client: httpx.Client, path: str, body: dict, done_statuses: set[str]) -> dict:
    started = time.time()
    while time.time() - started < MAX_WAIT:
        resp = client.post(path, json=body)
        resp.raise_for_status()
        data = resp.json()["data"]
        status = data.get("status", "")
        if status in done_statuses or data.get("already_prepared") or data.get("has_report"):
            return data
        print(f"  … {path} status={status}")
        time.sleep(POLL_SECONDS)
    raise TimeoutError(f"Timed out waiting for {path}")


def wait_graph_task(client: httpx.Client, task_id: str) -> None:
    started = time.time()
    while time.time() - started < MAX_WAIT:
        resp = client.get(f"/api/graph/task/{task_id}")
        resp.raise_for_status()
        data = resp.json()["data"]
        status = data.get("status", "")
        if status in {"completed", "failed"}:
            if status == "failed":
                raise RuntimeError(data.get("message", "Graph build failed"))
            return
        print(f"  … graph task status={status}")
        time.sleep(POLL_SECONDS)
    raise TimeoutError("Graph build timed out")


def main() -> None:
    BRIEF.parent.mkdir(parents=True, exist_ok=True)
    if not BRIEF.exists():
        BRIEF.write_text(
            "# Personal investor brief\n\n"
            "Holdings: VTI 120 shares, BND 80 shares, AAPL 25 shares.\n"
            "Scenario: Fed cuts rates 50bps while CPI remains sticky.\n"
            "Question: How might a 60/40 ETF portfolio react over 90 days?\n",
            encoding="utf-8",
        )

    with httpx.Client(base_url=BASE, timeout=120.0) as client:
        health = client.get("/health")
        health.raise_for_status()

        with BRIEF.open("rb") as f:
            resp = client.post(
                "/api/graph/ontology/generate",
                data={
                    "simulation_requirement": (
                        "Retail investors with ETF-heavy portfolios react to a 50bps Fed cut "
                        "while inflation stays sticky."
                    ),
                    "project_name": "Apex Personal Investor Live",
                },
                files={"files": ("investor_brief.md", f, "text/markdown")},
            )
        resp.raise_for_status()
        project_id = resp.json()["data"]["project_id"]
        print("project_id:", project_id)

        resp = client.post(
            "/api/graph/build",
            json={"project_id": project_id},
        )
        resp.raise_for_status()
        task_id = resp.json()["data"]["task_id"]
        wait_graph_task(client, task_id)
        project = client.get(f"/api/graph/project/{project_id}").json()["data"]
        graph_id = project["graph_id"]
        print("graph_id:", graph_id)

        resp = client.post("/api/simulation/create", json={"project_id": project_id, "graph_id": graph_id})
        resp.raise_for_status()
        simulation_id = resp.json()["data"]["simulation_id"]
        print("simulation_id:", simulation_id)

        resp = client.post(
            "/api/simulation/prepare",
            json={"simulation_id": simulation_id, "parallel_profile_count": 3},
        )
        resp.raise_for_status()
        if resp.json()["data"].get("task_id"):
            wait_until(
                client,
                "/api/simulation/prepare/status",
                {"simulation_id": simulation_id},
                {"ready"},
            )

        resp = client.post(
            "/api/simulation/start",
            json={"simulation_id": simulation_id, "max_rounds": 5, "platform": "twitter"},
        )
        resp.raise_for_status()

        started = time.time()
        while time.time() - started < MAX_WAIT:
            detail = client.get(f"/api/simulation/{simulation_id}/run-status/detail").json()["data"]
            status = detail.get("runner_status") or detail.get("status")
            print("  … run status:", status)
            if status in {"completed", "stopped", "failed", "idle"}:
                break
            time.sleep(POLL_SECONDS)

        resp = client.post("/api/report/generate", json={"simulation_id": simulation_id})
        resp.raise_for_status()
        if resp.json()["data"].get("task_id"):
            wait_until(
                client,
                "/api/report/generate/status",
                {"task_id": resp.json()["data"]["task_id"]},
                {"completed", "failed"},
            )

    env_path = ROOT / ".env"
    lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
    out = []
    seen = False
    for line in lines:
        if line.startswith("MIROFISH_DEFAULT_SIMULATION_ID="):
            out.append(f"MIROFISH_DEFAULT_SIMULATION_ID={simulation_id}")
            seen = True
        else:
            out.append(line)
    if not seen:
        out.append(f"MIROFISH_DEFAULT_SIMULATION_ID={simulation_id}")
    env_path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(json.dumps({"simulation_id": simulation_id, "project_id": project_id, "graph_id": graph_id}))


if __name__ == "__main__":
    try:
        main()
    except httpx.HTTPError as exc:
        print("Bootstrap failed:", exc, file=sys.stderr)
        print("Tip: run scripts/setup_mirofish.py and add real keys to ~/.config/apex-ledger/mirofish.env")
        sys.exit(1)
