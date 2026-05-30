"""Create and cache MiroFish simulations per investor question topic."""

from __future__ import annotations

import hashlib
import json
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import httpx

from ..council.topics import TopicAnalysis
from .keys import load_mirofish_keys

POLL_SECONDS = 5
MAX_WAIT_SECONDS = 3600
DEFAULT_MAX_ROUNDS = 5
DEFAULT_FIXTURE_SIMULATION = "sim_apex_personal_investor"


@dataclass
class FactoryResult:
    simulation_id: str | None
    status: str
    message: str
    cache_key: str = ""
    project_id: str | None = None


@dataclass
class FactoryJob:
    cache_key: str
    status: str = "running"
    message: str = "Starting simulation factory…"
    simulation_id: str | None = None
    error: str | None = None
    _thread: threading.Thread | None = field(default=None, repr=False)


class SimulationFactory:
    def __init__(
        self,
        base_url: str,
        cache_path: Path,
        briefs_dir: Path,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.cache_path = cache_path
        self.briefs_dir = briefs_dir
        self.briefs_dir.mkdir(parents=True, exist_ok=True)
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self._jobs: dict[str, FactoryJob] = {}
        self._lock = threading.Lock()

    def cache_key_for(self, topic: TopicAnalysis, question: str) -> str:
        digest = hashlib.sha256(question.strip().lower().encode()).hexdigest()[:16]
        return f"{topic.primary_topic}:{digest}"

    def lookup_cached(self, cache_key: str) -> str | None:
        cache = self._read_cache()
        entry = cache.get(cache_key)
        if entry and entry.get("simulation_id"):
            return entry["simulation_id"]
        return None

    def resolve_simulation(
        self,
        question: str,
        topic: TopicAnalysis,
        job_id: str | None = None,
        on_complete: Callable[[FactoryResult], None] | None = None,
    ) -> FactoryResult:
        keys = load_mirofish_keys()
        cache_key = self.cache_key_for(topic, question)
        cached = self.lookup_cached(cache_key)
        if cached:
            return FactoryResult(
                simulation_id=cached,
                status="cached",
                message=f"Using cached simulation {cached} for this topic.",
                cache_key=cache_key,
            )

        if not keys.valid:
            fixture = "sim_apex_personal_investor"
            return FactoryResult(
                simulation_id=fixture,
                status="fixture",
                message=(
                    "Live simulation requires real LLM + Zep keys in "
                    "~/.config/apex-ledger/mirofish.env — using demo simulation."
                ),
                cache_key=cache_key,
            )

        job_key = job_id or cache_key
        with self._lock:
            if job_key in self._jobs and self._jobs[job_key].status == "running":
                job = self._jobs[job_key]
                return FactoryResult(
                    simulation_id=job.simulation_id,
                    status="running",
                    message=job.message,
                    cache_key=cache_key,
                )
            job = FactoryJob(cache_key=cache_key)
            self._jobs[job_key] = job

        def runner() -> None:
            try:
                result = self._run_pipeline(question, topic, cache_key)
                job.status = result.status
                job.message = result.message
                job.simulation_id = result.simulation_id
                if on_complete:
                    on_complete(result)
            except Exception as exc:  # noqa: BLE001
                result = self._fixture_fallback(cache_key, exc)
                job.status = result.status
                job.message = result.message
                job.simulation_id = result.simulation_id
                job.error = str(exc)
                if on_complete:
                    on_complete(result)

        thread = threading.Thread(target=runner, daemon=True)
        job._thread = thread
        thread.start()
        return FactoryResult(
            simulation_id=None,
            status="running",
            message="Building a new MiroFish simulation for your question (1–15 min)…",
            cache_key=cache_key,
        )

    def job_status(self, job_id: str) -> FactoryResult | None:
        job = self._jobs.get(job_id)
        if not job:
            cached = self.lookup_cached(job_id)
            if cached:
                return FactoryResult(
                    simulation_id=cached,
                    status="cached",
                    message=f"Simulation {cached} ready.",
                    cache_key=job_id,
                )
            return None
        return FactoryResult(
            simulation_id=job.simulation_id,
            status=job.status,
            message=job.message,
            cache_key=job.cache_key,
        )

    @staticmethod
    def _friendly_pipeline_error(exc: Exception) -> str:
        text = str(exc)
        if "insufficient_quota" in text or "exceeded your current quota" in text:
            return "OpenAI API quota exceeded — add billing or switch LLM keys"
        if "429" in text:
            return "LLM rate limit hit — retry later or use demo simulation mode"
        return text[:220]

    def _fixture_fallback(self, cache_key: str, exc: Exception) -> FactoryResult:
        reason = self._friendly_pipeline_error(exc)
        return FactoryResult(
            simulation_id=DEFAULT_FIXTURE_SIMULATION,
            status="fixture",
            message=(
                f"MiroFish live simulation unavailable ({reason}). "
                f"Using demo simulation {DEFAULT_FIXTURE_SIMULATION}."
            ),
            cache_key=cache_key,
        )

    def _run_pipeline(self, question: str, topic: TopicAnalysis, cache_key: str) -> FactoryResult:
        brief_path = self._write_brief(question, topic)
        requirement = self._simulation_requirement(question, topic)

        with httpx.Client(base_url=self.base_url, timeout=180.0) as client:
            client.get("/health").raise_for_status()
            with brief_path.open("rb") as handle:
                resp = client.post(
                    "/api/graph/ontology/generate",
                    data={
                        "simulation_requirement": requirement,
                        "project_name": f"Apex — {topic.topic_label}",
                        "additional_context": question,
                    },
                    files={"files": (brief_path.name, handle, "text/markdown")},
                )
            resp.raise_for_status()
            project_id = resp.json()["data"]["project_id"]

            resp = client.post("/api/graph/build", json={"project_id": project_id})
            resp.raise_for_status()
            task_id = resp.json()["data"]["task_id"]
            self._wait_graph_task(client, task_id)

            project = client.get(f"/api/graph/project/{project_id}").json()["data"]
            graph_id = project["graph_id"]

            resp = client.post(
                "/api/simulation/create",
                json={"project_id": project_id, "graph_id": graph_id, "enable_reddit": False},
            )
            resp.raise_for_status()
            simulation_id = resp.json()["data"]["simulation_id"]

            resp = client.post(
                "/api/simulation/prepare",
                json={
                    "simulation_id": simulation_id,
                    "parallel_profile_count": 3,
                    "use_llm_for_profiles": True,
                },
            )
            resp.raise_for_status()
            data = resp.json()["data"]
            if not data.get("already_prepared") and data.get("task_id"):
                self._wait_prepare(client, simulation_id, data["task_id"])

            resp = client.post(
                "/api/simulation/start",
                json={
                    "simulation_id": simulation_id,
                    "platform": "twitter",
                    "max_rounds": DEFAULT_MAX_ROUNDS,
                },
            )
            resp.raise_for_status()
            self._wait_simulation_complete(client, simulation_id)

            resp = client.post("/api/report/generate", json={"simulation_id": simulation_id})
            resp.raise_for_status()
            report_data = resp.json()["data"]
            if report_data.get("task_id"):
                self._wait_report(client, report_data["task_id"])

        self._write_cache(cache_key, simulation_id, project_id, question, topic.primary_topic)
        return FactoryResult(
            simulation_id=simulation_id,
            status="ready",
            message=f"Live simulation {simulation_id} is ready.",
            cache_key=cache_key,
            project_id=project_id,
        )

    def _wait_graph_task(self, client: httpx.Client, task_id: str) -> None:
        started = time.time()
        while time.time() - started < MAX_WAIT_SECONDS:
            resp = client.get(f"/api/graph/task/{task_id}")
            resp.raise_for_status()
            status = resp.json()["data"].get("status", "")
            if status in {"completed", "failed"}:
                if status == "failed":
                    raise RuntimeError(resp.json()["data"].get("message", "Graph build failed"))
                return
            time.sleep(POLL_SECONDS)
        raise TimeoutError("Graph build timed out")

    def _wait_prepare(self, client: httpx.Client, simulation_id: str, task_id: str) -> None:
        started = time.time()
        while time.time() - started < MAX_WAIT_SECONDS:
            resp = client.post(
                "/api/simulation/prepare/status",
                json={"task_id": task_id, "simulation_id": simulation_id},
            )
            resp.raise_for_status()
            data = resp.json()["data"]
            if data.get("already_prepared") or data.get("status") in {"ready", "completed"}:
                return
            time.sleep(POLL_SECONDS)
        raise TimeoutError("Simulation prepare timed out")

    def _wait_simulation_complete(self, client: httpx.Client, simulation_id: str) -> None:
        started = time.time()
        while time.time() - started < MAX_WAIT_SECONDS:
            resp = client.get(f"/api/simulation/{simulation_id}/run-status/detail")
            resp.raise_for_status()
            detail = resp.json().get("data", {})
            status = detail.get("runner_status") or detail.get("status") or ""
            if status in {"completed", "stopped", "failed", "idle"}:
                return
            time.sleep(POLL_SECONDS)
        raise TimeoutError("Simulation run timed out")

    def _wait_report(self, client: httpx.Client, task_id: str) -> None:
        started = time.time()
        while time.time() - started < MAX_WAIT_SECONDS:
            resp = client.post("/api/report/generate/status", json={"task_id": task_id})
            resp.raise_for_status()
            status = resp.json()["data"].get("status", "")
            if status in {"completed", "failed"}:
                if status == "failed":
                    raise RuntimeError("Report generation failed")
                return
            time.sleep(POLL_SECONDS)
        raise TimeoutError("Report generation timed out")

    def _write_brief(self, question: str, topic: TopicAnalysis) -> Path:
        path = self.briefs_dir / f"{topic.primary_topic}.md"
        if not path.exists():
            path.write_text(
                f"# Apex investor brief — {topic.topic_label}\n\n"
                f"User question: {question}\n\n"
                f"Context: {topic.direct_answer}\n",
                encoding="utf-8",
            )
        return path

    @staticmethod
    def _simulation_requirement(question: str, topic: TopicAnalysis) -> str:
        return (
            f"Simulate how personal investors react to this scenario: {question}. "
            f"Focus area: {topic.topic_label}. "
            "Include retail investors, commentators, and risk-aware savers."
        )

    def _read_cache(self) -> dict:
        if not self.cache_path.exists():
            return {}
        return json.loads(self.cache_path.read_text(encoding="utf-8"))

    def _write_cache(
        self,
        cache_key: str,
        simulation_id: str,
        project_id: str,
        question: str,
        topic: str,
    ) -> None:
        cache = self._read_cache()
        cache[cache_key] = {
            "simulation_id": simulation_id,
            "project_id": project_id,
            "question": question,
            "topic": topic,
            "created_at": time.time(),
        }
        self.cache_path.write_text(json.dumps(cache, indent=2), encoding="utf-8")
