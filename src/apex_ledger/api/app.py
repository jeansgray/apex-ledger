"""FastAPI surface for Apex Ledger."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from ..config import get_settings
from ..council.brief import ensure_friendly_brief
from ..council.graph import CouncilOrchestrator

WEB_DIR = Path(__file__).resolve().parent.parent / "web"

app = FastAPI(title="Apex Ledger", version="0.1.0")
_settings = get_settings()
_orchestrator = CouncilOrchestrator(_settings)


class CouncilRunRequest(BaseModel):
    question: str = Field(min_length=3)
    simulation_id: str | None = None
    seed_demo: bool = True
    cash_to_deploy: float = Field(default=1000.0, gt=0)
    use_live_simulation: bool = True


class GateApprovalRequest(BaseModel):
    gate_kind: str
    approved: bool


@app.get("/health")
def health() -> dict:
    mirofish_ok = False
    try:
        mirofish_ok = _orchestrator.mirofish.health().get("status") == "ok"
    except Exception:
        mirofish_ok = False
    kronos_ok = False
    try:
        kronos_ok = _orchestrator.kronos.health().get("status") == "ok"
    except Exception:
        kronos_ok = False
    return {
        "status": "ok",
        "service": "apex-ledger",
        "mirofish": "ok" if mirofish_ok else "unreachable",
        "kronos": "ok" if kronos_ok else "unreachable",
        "keys": _orchestrator.keys_status(),
        "default_simulation_id": _settings.mirofish_default_simulation_id,
    }


@app.get("/config")
def public_config() -> dict:
    _orchestrator.ledger.seed_demo_data()
    return {
        "default_simulation_id": _settings.mirofish_default_simulation_id,
        "mirofish_base_url": _settings.mirofish_base_url,
        "kronos_base_url": _settings.kronos_base_url,
        "keys": _orchestrator.keys_status(),
        "default_cash_to_deploy": _settings.apex_default_cash_to_deploy,
        "ledger_mode": "demo" if _orchestrator.ledger.is_demo_portfolio() else "personal",
        "holdings_count": len(_orchestrator.ledger.list_holdings()),
    }


@app.get("/")
def index() -> FileResponse:
    response = FileResponse(WEB_DIR / "index.html")
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    return response


def _public_run(state) -> dict:
    payload = state.model_dump(mode="json")
    payload["friendly_brief"] = ensure_friendly_brief(state)
    payload["topic_analysis"] = state.topic_analysis or {}
    return payload


app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


@app.post("/council/run")
def council_run(body: CouncilRunRequest) -> JSONResponse:
    state = _orchestrator.run(
        user_question=body.question,
        simulation_id=body.simulation_id,
        seed_demo=body.seed_demo,
        cash_to_deploy=body.cash_to_deploy,
        use_live_simulation=body.use_live_simulation,
    )
    return JSONResponse(_public_run(state))


@app.get("/council/run/{run_id}")
def get_run(run_id: str) -> JSONResponse:
    state = _orchestrator._runs.get(run_id)
    if not state:
        raise HTTPException(status_code=404, detail="Run not found")
    return JSONResponse(_public_run(state))


@app.post("/council/run/{run_id}/refresh")
def refresh_run(run_id: str) -> JSONResponse:
    state = _orchestrator.refresh_run(run_id)
    if not state:
        raise HTTPException(status_code=404, detail="Run not found")
    return JSONResponse(_public_run(state))


@app.post("/council/run/{run_id}/approve")
def approve_gate(run_id: str, body: GateApprovalRequest) -> JSONResponse:
    state = _orchestrator._runs.get(run_id)
    if not state:
        raise HTTPException(status_code=404, detail="Run not found")
    updated = _orchestrator.approve_gate(state, body.gate_kind, body.approved)
    return JSONResponse(_public_run(updated))


@app.get("/ledger/portfolio")
def portfolio() -> dict:
    _orchestrator.ledger.seed_demo_data()
    return _orchestrator.ledger.portfolio_snapshot()
