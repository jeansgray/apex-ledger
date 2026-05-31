"""FastAPI surface for Apex Ledger."""

from __future__ import annotations

from pathlib import Path

from datetime import date

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from ..config import get_settings
from ..council.brief import ensure_friendly_brief
from ..council.graph import CouncilOrchestrator
from ..integrations.plaid_client import PlaidClient, PlaidError
from ..integrations.schwab_client import SchwabClient, SchwabError
from ..integrations.schwab_import import parse_schwab_csv
from ..integrations.store import IntegrationStore

WEB_DIR = Path(__file__).resolve().parent.parent / "web"

app = FastAPI(title="Apex Ledger", version="0.1.0")
_settings = get_settings()
_orchestrator = CouncilOrchestrator(_settings)


class CouncilRunRequest(BaseModel):
    question: str = Field(min_length=3)
    simulation_id: str | None = None
    seed_demo: bool = True
    cash_to_deploy: float = Field(default=1000.0, gt=0)
    use_live_simulation: bool | None = None


class GateApprovalRequest(BaseModel):
    gate_kind: str
    approved: bool


class HoldingWrite(BaseModel):
    symbol: str = Field(min_length=1, max_length=12)
    quantity: float = Field(gt=0)
    cost_basis: float | None = Field(default=None, ge=0)
    account: str = Field(default="brokerage", min_length=1)


class TransactionWrite(BaseModel):
    posted_on: str = Field(description="ISO date YYYY-MM-DD")
    description: str = Field(min_length=1)
    amount: float = Field(description="Negative for outflows")
    account: str = Field(default="checking", min_length=1)


class PlaidExchangeRequest(BaseModel):
    public_token: str = Field(min_length=1)


def _integration_store() -> IntegrationStore:
    return IntegrationStore(_settings.apex_integrations_file)


def _plaid_client() -> PlaidClient:
    return PlaidClient(_settings.plaid_client_id, _settings.plaid_secret, _settings.plaid_env)


def _schwab_client() -> SchwabClient:
    return SchwabClient(
        _settings.schwab_app_key,
        _settings.schwab_app_secret,
        _settings.schwab_redirect_uri,
    )


def _integrations_status() -> dict:
    store = _integration_store()
    plaid = store.get_plaid()
    schwab = store.get_schwab()
    return {
        "plaid_configured": bool(_settings.plaid_client_id and _settings.plaid_secret),
        "plaid_connected": bool(plaid and plaid.get("access_token")),
        "plaid_institution": (plaid or {}).get("institution", ""),
        "schwab_configured": bool(_settings.schwab_app_key and _settings.schwab_app_secret),
        "schwab_connected": bool(schwab and schwab.get("access_token")),
        "schwab_callback_url": _settings.schwab_redirect_uri,
        "schwab_import": "csv_backup",
        "schwab_oauth": "trader_api",
    }


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
        "integrations": _integrations_status(),
        "use_live_simulation": _settings.apex_use_live_simulation,
        "collaborator_parity": {
            "same_dashboard": "yes_when_all_services_run",
            "same_output": "same_question_same_holdings_same_keys_mode",
            "personal_data": "local_per_machine_in_data_ledger_db",
        },
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
    snap = _orchestrator.ledger.portfolio_snapshot()
    snap["ledger_mode"] = "demo" if _orchestrator.ledger.is_demo_portfolio() else "personal"
    return snap


@app.get("/ledger/detail")
def ledger_detail() -> dict:
    _orchestrator.ledger.seed_demo_data()
    detail = _orchestrator.ledger.ledger_detail()
    detail["ledger_mode"] = "demo" if _orchestrator.ledger.is_demo_portfolio() else "personal"
    detail["integrations"] = _integrations_status()
    return detail


@app.post("/ledger/holdings")
def add_holding(body: HoldingWrite) -> dict:
    hid = _orchestrator.ledger.add_holding(
        body.symbol, body.quantity, body.cost_basis, body.account
    )
    return {"id": hid, "ledger_mode": "demo" if _orchestrator.ledger.is_demo_portfolio() else "personal"}


@app.put("/ledger/holdings/{holding_id}")
def update_holding(holding_id: int, body: HoldingWrite) -> dict:
    _orchestrator.ledger.update_holding(
        holding_id, body.symbol, body.quantity, body.cost_basis, body.account
    )
    return {"ok": True}


@app.delete("/ledger/holdings/{holding_id}")
def remove_holding(holding_id: int) -> dict:
    _orchestrator.ledger.delete_holding(holding_id)
    return {"ok": True}


@app.post("/ledger/transactions")
def add_transaction(body: TransactionWrite) -> dict:
    try:
        posted = date.fromisoformat(body.posted_on)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid posted_on date") from exc
    tid = _orchestrator.ledger.add_transaction(
        posted, body.description, body.amount, body.account
    )
    return {"id": tid}


@app.delete("/ledger/transactions/{transaction_id}")
def remove_transaction(transaction_id: int) -> dict:
    _orchestrator.ledger.delete_transaction(transaction_id)
    return {"ok": True}


@app.post("/ledger/reset-demo")
def reset_demo_ledger() -> dict:
    _orchestrator.ledger.clear_portfolio()
    with _orchestrator.ledger.connection() as conn:
        _orchestrator.ledger._insert_demo_rows(conn)
    detail = _orchestrator.ledger.ledger_detail()
    detail["ledger_mode"] = "demo"
    return detail


@app.get("/watchlist")
def get_watchlist() -> dict:
    return {"symbols": _orchestrator.ledger.list_watchlist()}


class WatchlistAdd(BaseModel):
    symbol: str = Field(min_length=1, max_length=12)


@app.post("/watchlist")
def add_watchlist(body: WatchlistAdd) -> dict:
    _orchestrator.ledger.add_to_watchlist(body.symbol)
    return {"symbols": _orchestrator.ledger.list_watchlist()}


@app.delete("/watchlist/{symbol}")
def remove_watchlist(symbol: str) -> dict:
    _orchestrator.ledger.remove_from_watchlist(symbol)
    return {"symbols": _orchestrator.ledger.list_watchlist()}


@app.post("/ledger/import-csv")
async def import_holdings_csv(file: UploadFile = File(...)) -> dict:
    import csv
    import io

    raw = (await file.read()).decode("utf-8")
    rows: list[tuple[str, float, float | None, str]] = []
    reader = csv.DictReader(io.StringIO(raw))
    for line in reader:
        symbol = (line.get("symbol") or "").strip().upper()
        if not symbol:
            continue
        quantity = float(line["quantity"])
        cost_raw = (line.get("cost_basis") or "").strip()
        cost_basis = float(cost_raw) if cost_raw else None
        account = (line.get("account") or "brokerage").strip() or "brokerage"
        rows.append((symbol, quantity, cost_basis, account))
    if not rows:
        raise HTTPException(status_code=400, detail="No holdings found in CSV")
    _orchestrator.ledger.clear_portfolio()
    count = _orchestrator.ledger.replace_holdings(rows)
    detail = _orchestrator.ledger.ledger_detail()
    detail["imported"] = count
    detail["ledger_mode"] = "demo" if _orchestrator.ledger.is_demo_portfolio() else "personal"
    return detail


@app.get("/integrations/status")
def integrations_status() -> dict:
    return _integrations_status()


@app.post("/integrations/plaid/link-token")
def plaid_link_token() -> dict:
    try:
        token = _plaid_client().create_link_token()
    except PlaidError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"link_token": token}


@app.post("/integrations/plaid/exchange")
def plaid_exchange(body: PlaidExchangeRequest) -> dict:
    try:
        access_token, item_id = _plaid_client().exchange_public_token(body.public_token)
        _integration_store().set_plaid(access_token, item_id)
    except PlaidError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "item_id": item_id}


@app.post("/integrations/plaid/sync")
def plaid_sync() -> dict:
    plaid = _integration_store().get_plaid()
    if not plaid or not plaid.get("access_token"):
        raise HTTPException(status_code=400, detail="Connect a bank via Plaid first")
    try:
        synced = _plaid_client().sync_ledger_data(plaid["access_token"])
    except PlaidError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if synced["holdings"]:
        _orchestrator.ledger.replace_holdings(synced["holdings"])
    tx_count = 0
    if synced["transactions"]:
        tx_count = _orchestrator.ledger.import_transactions_bulk(synced["transactions"])
    detail = _orchestrator.ledger.ledger_detail()
    detail["synced"] = {"holdings": len(synced["holdings"]), "transactions": tx_count}
    detail["ledger_mode"] = "demo" if _orchestrator.ledger.is_demo_portfolio() else "personal"
    detail["integrations"] = _integrations_status()
    return detail


@app.delete("/integrations/plaid")
def plaid_disconnect() -> dict:
    _integration_store().clear_plaid()
    return {"ok": True}


@app.get("/oauth/schwab/start")
def schwab_oauth_start() -> RedirectResponse:
    try:
        client = _schwab_client()
    except SchwabError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    state = _integration_store().create_oauth_state("schwab")
    return RedirectResponse(client.authorize_url(state))


@app.get("/oauth/schwab/callback")
def schwab_oauth_callback(code: str = "", state: str = "", error: str = "") -> HTMLResponse:
    if error:
        return HTMLResponse(
            f"<html><body><p>Schwab authorization failed: {error}</p>"
            f'<p><a href="/">Back to Apex Ledger</a></p></body></html>',
            status_code=400,
        )
    if not code or not _integration_store().consume_oauth_state(state, "schwab"):
        return HTMLResponse(
            "<html><body><p>Invalid or expired Schwab OAuth state.</p>"
            '<p><a href="/">Back to Apex Ledger</a></p></body></html>',
            status_code=400,
        )
    try:
        tokens = _schwab_client().exchange_code(code)
        _integration_store().set_schwab(tokens)
    except SchwabError as exc:
        return HTMLResponse(
            f"<html><body><p>Schwab token exchange failed: {exc}</p>"
            f'<p><a href="/">Back to Apex Ledger</a></p></body></html>',
            status_code=400,
        )
    return HTMLResponse(
        "<html><body><p>Schwab connected. You can close this tab and click "
        "<strong>Sync Schwab</strong> in Apex Ledger.</p>"
        '<script>if (window.opener) { window.opener.location="/?schwab=connected"; window.close(); }</script>'
        '<p><a href="/?schwab=connected">Continue to dashboard</a></p></body></html>'
    )


@app.post("/integrations/schwab/sync")
def schwab_sync() -> dict:
    store = _integration_store()
    schwab = store.get_schwab()
    if not schwab or not schwab.get("access_token"):
        raise HTTPException(status_code=400, detail="Connect Schwab via OAuth first")
    try:
        synced = _schwab_client().sync_ledger_data(dict(schwab))
    except SchwabError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    store.set_schwab(synced["tokens"])
    if synced["holdings"]:
        _orchestrator.ledger.replace_holdings(synced["holdings"])
    tx_count = 0
    if synced["transactions"]:
        tx_count = _orchestrator.ledger.import_transactions_bulk(synced["transactions"])
    detail = _orchestrator.ledger.ledger_detail()
    detail["synced"] = {
        "holdings": len(synced["holdings"]),
        "transactions": tx_count,
        "accounts": synced.get("accounts", 0),
    }
    detail["ledger_mode"] = "demo" if _orchestrator.ledger.is_demo_portfolio() else "personal"
    detail["integrations"] = _integrations_status()
    return detail


@app.delete("/integrations/schwab")
def schwab_disconnect() -> dict:
    _integration_store().clear_schwab()
    return {"ok": True}


@app.post("/ledger/import-schwab")
async def import_schwab_csv(file: UploadFile = File(...)) -> dict:
    raw = (await file.read()).decode("utf-8")
    try:
        parsed = parse_schwab_csv(raw)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if parsed["holdings"]:
        _orchestrator.ledger.replace_holdings(parsed["holdings"])
    tx_count = 0
    if parsed["transactions"]:
        tx_count = _orchestrator.ledger.import_transactions_bulk(parsed["transactions"])
    detail = _orchestrator.ledger.ledger_detail()
    detail["imported"] = {
        "kind": parsed["kind"],
        "holdings": len(parsed["holdings"]),
        "transactions": tx_count,
    }
    detail["ledger_mode"] = "demo" if _orchestrator.ledger.is_demo_portfolio() else "personal"
    return detail
