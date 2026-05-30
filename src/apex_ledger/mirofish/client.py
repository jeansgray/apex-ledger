"""HTTP client for MiroFish (AGPL service boundary — no code import from vendor/)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx


class MiroFishError(RuntimeError):
    pass


class MiroFishClient:
    def __init__(
        self,
        base_url: str,
        timeout: float = 120.0,
        insights_dir: Path | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.insights_dir = insights_dir or Path("./data/mirofish_insights")

    def health(self) -> dict[str, Any]:
        return self._get("/health")

    def get_simulation(self, simulation_id: str) -> dict[str, Any]:
        payload = self._get(f"/api/simulation/{simulation_id}")
        return payload.get("data", payload)

    def batch_interview(
        self,
        simulation_id: str,
        prompts: list[str],
        max_agents: int = 3,
    ) -> dict[str, Any]:
        interviews = [
            {"agent_id": idx, "prompt": prompt}
            for idx, prompt in enumerate(prompts[:max_agents])
        ]
        body = {
            "simulation_id": simulation_id,
            "interviews": interviews,
            "platform": "twitter",
        }
        payload = self._post("/api/simulation/interview/batch", body)
        return payload.get("data", payload)

    def generate_report(self, simulation_id: str, force_regenerate: bool = False) -> dict[str, Any]:
        body = {"simulation_id": simulation_id, "force_regenerate": force_regenerate}
        payload = self._post("/api/report/generate", body)
        return payload.get("data", payload)

    def report_generate_status(self, task_id: str) -> dict[str, Any]:
        payload = self._post("/api/report/generate/status", {"task_id": task_id})
        return payload.get("data", payload)

    def get_report_by_simulation(self, simulation_id: str) -> dict[str, Any] | None:
        try:
            payload = self._get(f"/api/report/by-simulation/{simulation_id}")
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return None
            raise
        if not payload.get("success"):
            return None
        return payload.get("data")

    def _load_fixture_insights(self, simulation_id: str) -> list[str]:
        path = self.insights_dir / f"{simulation_id}.json"
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        return [str(item) for item in data.get("insights", [])]

    def fetch_scenario_insights(
        self,
        simulation_id: str,
        user_question: str,
    ) -> list[str]:
        """Pull simulation context via interview, report, timeline, and local fixtures."""
        insights: list[str] = []

        try:
            interview = self.batch_interview(
                simulation_id,
                prompts=[
                    f"As a retail investor persona, how would '{user_question}' affect your portfolio outlook?",
                    "What is the single biggest risk you see in the next 90 days?",
                ],
            )
            results = interview.get("result", {}).get("results", interview.get("results", {}))
            if isinstance(results, dict):
                for entry in results.values():
                    response = entry.get("response") or entry.get("summary")
                    if response:
                        insights.append(str(response))
        except (MiroFishError, httpx.HTTPError):
            insights.extend(self._load_fixture_insights(simulation_id))

        report = self.get_report_by_simulation(simulation_id)
        if report:
            summary = None
            outline = report.get("outline") or {}
            summary = outline.get("summary") or report.get("simulation_requirement")
            if summary:
                insights.append(f"Simulation report summary: {summary}")

        try:
            timeline = self._get(f"/api/simulation/{simulation_id}/timeline")
            if timeline.get("success"):
                for event in timeline.get("data", {}).get("timeline", [])[:5]:
                    if isinstance(event, dict):
                        desc = (
                            f"Round {event.get('round_num')}: "
                            f"{event.get('twitter_actions', 0)} twitter actions"
                        )
                        insights.append(f"Timeline: {desc}")
                    else:
                        insights.append(f"Timeline: {event}")
        except httpx.HTTPError:
            pass

        if not insights:
            insights.extend(self._load_fixture_insights(simulation_id))

        return insights

    def _get(self, path: str) -> dict[str, Any]:
        with httpx.Client(base_url=self.base_url, timeout=self.timeout) as client:
            response = client.get(path)
            response.raise_for_status()
            return response.json()

    def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        with httpx.Client(base_url=self.base_url, timeout=self.timeout) as client:
            response = client.post(path, json=body)
            response.raise_for_status()
            data = response.json()
            if not data.get("success", True):
                raise MiroFishError(data.get("error") or "MiroFish request failed")
            return data
