"""Council orchestration — simulation factory + investment recommendations."""

from __future__ import annotations

from pathlib import Path

import httpx

from ..config import Settings
from ..data.alpha_vantage import AlphaVantageClient
from ..ledger.reconciliation import propose_reconciliation
from ..ledger.store import LedgerStore
from ..kronos.client import KronosClient
from ..mirofish.client import MiroFishClient, MiroFishError
from ..mirofish.factory import FactoryResult, SimulationFactory
from ..mirofish.keys import load_mirofish_keys
from ..skills.loader import SkillRegistry
from .challenge import run_signal_challenge
from .presentation import build_friendly_brief
from .recommendations import build_suggested_moves
from .roster import COUNCIL_ROLES
from .topics import TopicAnalysis, analyze_question
from .state import CouncilRunState, HumanGate


def _topic_to_dict(topic: TopicAnalysis) -> dict:
    return {
        "primary_topic": topic.primary_topic,
        "topic_label": topic.topic_label,
        "direct_answer": topic.direct_answer,
        "research_bullets": topic.research_bullets,
        "scenario_base": topic.scenario_base,
        "scenario_upside": topic.scenario_upside,
        "scenario_downside": topic.scenario_downside,
        "action_templates": [
            {"priority": p, "title": t, "detail": d} for p, t, d in topic.action_templates
        ],
        "simulation_note": topic.simulation_note,
    }


class CouncilOrchestrator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.ledger = LedgerStore(settings.apex_ledger_db)
        self.mirofish = MiroFishClient(
            settings.mirofish_base_url,
            insights_dir=settings.apex_data_dir / "mirofish_insights",
        )
        self.factory = SimulationFactory(
            settings.mirofish_base_url,
            settings.apex_simulation_cache,
            settings.apex_data_dir / "briefs",
        )
        self.kronos = KronosClient(
            settings.kronos_base_url,
            fixtures_dir=Path("./fixtures/kronos"),
        )
        self.skills = SkillRegistry(settings.apex_skills_dir, settings.apex_skill_manifest)
        self.alpha_vantage = AlphaVantageClient(
            settings.alpha_vantage_api_key,
            cache_dir=settings.apex_data_dir / "av_cache",
        )
        self._runs: dict[str, CouncilRunState] = {}

    def run(
        self,
        user_question: str,
        simulation_id: str | None = None,
        seed_demo: bool = True,
        cash_to_deploy: float | None = None,
        use_live_simulation: bool | None = None,
    ) -> CouncilRunState:
        topic = analyze_question(user_question)
        cash = cash_to_deploy or self.settings.apex_default_cash_to_deploy
        state = CouncilRunState(
            user_question=user_question,
            topic_analysis=_topic_to_dict(topic),
            cash_to_deploy=cash,
        )

        if seed_demo:
            self.ledger.seed_demo_data()

        try:
            self._run_ledger_steward(state)
            self._resolve_simulation(state, topic, simulation_id, use_live_simulation)
            self._run_reconciliation_proposer(state)
            self._run_research_curator(state, topic)
            self._run_quant_forecaster(state)
            self._run_scenario_cartographer(state, topic)
            self._run_signal_challenge(state)
            self._run_compliance_skeptic(state, topic)
            self._run_scenario_synthesizer(state, topic)
            self._run_recommendation_engine(state, topic)
            state.friendly_brief = build_friendly_brief(state, topic).model_dump()
            state.status = "awaiting_human" if state.simulation_factory.get("status") != "running" else "simulation_running"
        except Exception as exc:  # noqa: BLE001
            state.status = "failed"
            state.error = str(exc)

        self._runs[state.run_id] = state
        return state

    def refresh_run(self, run_id: str) -> CouncilRunState | None:
        state = self._runs.get(run_id)
        if not state:
            return None
        topic = analyze_question(state.user_question)
        factory_status = self.factory.job_status(state.run_id) or self.factory.job_status(
            state.simulation_factory.get("cache_key", "")
        )
        if factory_status and factory_status.status == "ready" and factory_status.simulation_id:
            state.simulation_id = factory_status.simulation_id
            state.simulation_factory = {
                "status": "ready",
                "message": factory_status.message,
                "cache_key": factory_status.cache_key,
                "simulation_id": factory_status.simulation_id,
            }
            self._run_scenario_cartographer(state, topic, force=True)
            self._run_signal_challenge(state)
            self._run_recommendation_engine(state, topic)
            state.friendly_brief = build_friendly_brief(state, topic).model_dump()
            state.status = "awaiting_human"
        elif factory_status and factory_status.status == "running":
            state.simulation_factory["message"] = factory_status.message
            state.status = "simulation_running"
        elif factory_status and factory_status.status == "failed":
            state.simulation_factory = {
                "status": "failed",
                "message": factory_status.message,
                "cache_key": factory_status.cache_key,
            }
            state.status = "awaiting_human"
        self._runs[run_id] = state
        return state

    def approve_gate(self, run_state: CouncilRunState, gate_kind: str, approved: bool) -> CouncilRunState:
        for gate in run_state.human_gates:
            if gate.kind == gate_kind and gate.approved is None:
                gate.approved = approved
                if approved and gate_kind == "reconciliation":
                    for proposal in run_state.reconciliation_proposals:
                        self.ledger.apply_reconciliation(
                            proposal["transaction_id"],
                            proposal["suggested_category"],
                            memo=f"Approved via council run {run_state.run_id}",
                        )
                    self.ledger.record_decision_memo(
                        run_state.run_id,
                        kind="reconciliation",
                        summary="User approved reconciliation proposals",
                        approved=True,
                        payload={"proposals": run_state.reconciliation_proposals},
                    )
                if approved and gate_kind in {"scenario_brief", "investment_moves"}:
                    self.ledger.record_decision_memo(
                        run_state.run_id,
                        kind=gate_kind,
                        summary=f"User approved {gate_kind}",
                        approved=True,
                        payload={
                            "scenario_brief": run_state.scenario_brief,
                            "suggested_moves": run_state.suggested_moves,
                        },
                    )
                if not approved:
                    self.ledger.record_decision_memo(
                        run_state.run_id,
                        kind=gate_kind,
                        summary=f"User rejected {gate_kind}",
                        approved=False,
                        payload=gate.payload,
                    )
                break
        if all(g.approved is not None for g in run_state.human_gates):
            run_state.status = "completed"
        topic = analyze_question(run_state.user_question)
        run_state.friendly_brief = build_friendly_brief(run_state, topic).model_dump()
        self._runs[run_state.run_id] = run_state
        return run_state

    def _resolve_simulation(
        self,
        state: CouncilRunState,
        topic: TopicAnalysis,
        simulation_id: str | None,
        use_live: bool | None,
    ) -> None:
        live = use_live if use_live is not None else self.settings.apex_use_live_simulation
        if simulation_id:
            state.simulation_id = simulation_id
            state.simulation_factory = {"status": "manual", "simulation_id": simulation_id, "message": "Using provided simulation."}
            return

        if not live:
            state.simulation_id = self.settings.mirofish_default_simulation_id or "sim_apex_personal_investor"
            state.simulation_factory = {"status": "fixture", "simulation_id": state.simulation_id}
            return

        def on_complete(result: FactoryResult) -> None:
            cached = self._runs.get(state.run_id)
            if not cached:
                return
            fixture = self.settings.mirofish_default_simulation_id or "sim_apex_personal_investor"
            sim_id = result.simulation_id or fixture
            if result.status == "failed":
                sim_id = fixture
                result = FactoryResult(
                    simulation_id=sim_id,
                    status="fixture",
                    message=result.message or f"Using demo simulation {sim_id}.",
                    cache_key=result.cache_key,
                )
            cached.simulation_factory = {
                "status": result.status,
                "message": result.message,
                "cache_key": result.cache_key,
                "simulation_id": sim_id,
            }
            cached.simulation_id = sim_id
            self.refresh_run(state.run_id)

        result = self.factory.resolve_simulation(
            state.user_question,
            topic,
            job_id=state.run_id,
            on_complete=on_complete,
        )
        state.simulation_factory = {
            "status": result.status,
            "message": result.message,
            "cache_key": result.cache_key,
            "simulation_id": result.simulation_id,
        }
        if result.simulation_id:
            state.simulation_id = result.simulation_id

    def _run_recommendation_engine(self, state: CouncilRunState, topic: TopicAnalysis) -> None:
        from ..kronos.models import SymbolForecast

        holdings = state.portfolio_snapshot.get("holdings", [])
        forecasts = [SymbolForecast.model_validate(f) for f in state.kronos_forecasts]
        moves = build_suggested_moves(
            topic,
            holdings,
            state.simulation_insights,
            cash_to_deploy=state.cash_to_deploy,
            kronos_forecasts=forecasts,
            confidence_multiplier=state.confidence_multiplier,
            signal_agreement=state.signal_agreement,
        )
        state.suggested_moves = [m.model_dump() for m in moves]
        state.human_gates.append(
            HumanGate(
                kind="investment_moves",
                summary=(
                    f"Review {len(moves)} suggested move(s) from Kronos + MiroFish council analysis."
                ),
                payload={"moves": state.suggested_moves},
            )
        )
        state.agent_outputs["recommendation_engine"] = f"Proposed {len(moves)} investment move(s)."

    def _run_quant_forecaster(self, state: CouncilRunState) -> None:
        if not self.settings.apex_use_kronos:
            state.agent_outputs["quant_forecaster"] = "Kronos forecasts disabled."
            return
        symbols = [h.get("symbol", "") for h in state.portfolio_snapshot.get("holdings", [])]
        try:
            forecasts = self.kronos.forecast_symbols(
                symbols,
                pred_len=self.settings.kronos_forecast_days,
            )
            state.kronos_forecasts = [f.model_dump() for f in forecasts]
            state.agent_outputs["quant_forecaster"] = (
                f"Forecast {len(forecasts)} symbol(s) over {self.settings.kronos_forecast_days} days."
            )
        except Exception as exc:  # noqa: BLE001
            state.agent_outputs["quant_forecaster"] = f"Kronos unavailable: {exc}"

    def _run_signal_challenge(self, state: CouncilRunState) -> None:
        from ..kronos.models import SymbolForecast

        forecasts = [SymbolForecast.model_validate(f) for f in state.kronos_forecasts]
        debate, agreement, multiplier = run_signal_challenge(forecasts, state.simulation_insights)
        state.council_debate = debate
        state.signal_agreement = agreement
        state.confidence_multiplier = multiplier
        state.agent_outputs["signal_challenge"] = f"Council signal agreement: {agreement}."

    def _run_ledger_steward(self, state: CouncilRunState) -> None:
        snapshot = self.ledger.portfolio_snapshot()
        unmatched = [t for t in self.ledger.list_transactions() if t.status.value == "unmatched"]
        state.portfolio_snapshot = snapshot
        state.unmatched_transactions = [t.model_dump(mode="json") for t in unmatched]
        state.agent_outputs["ledger_steward"] = (
            f"Loaded {len(snapshot['holdings'])} holdings; "
            f"{snapshot['unmatched_count']} unmatched transactions."
        )

    def _run_reconciliation_proposer(self, state: CouncilRunState) -> None:
        from ..ledger.models import Transaction

        txns = [Transaction.model_validate(t) for t in state.unmatched_transactions]
        proposals = propose_reconciliation(txns)
        state.reconciliation_proposals = [p.model_dump() for p in proposals]
        if proposals:
            state.human_gates.append(
                HumanGate(
                    kind="reconciliation",
                    summary=f"Review {len(proposals)} reconciliation proposal(s) before posting.",
                    payload={"proposals": state.reconciliation_proposals},
                )
            )

    def _run_research_curator(self, state: CouncilRunState, topic: TopicAnalysis) -> None:
        state.research_notes.extend(topic.research_bullets)
        holdings = state.portfolio_snapshot.get("holdings", [])
        if not holdings:
            state.agent_outputs["research_curator"] = "No holdings found."
            return

        symbols = list(dict.fromkeys(h["symbol"] for h in holdings[:5]))
        state.research_notes.append(f"[portfolio] Current holdings: {', '.join(symbols)}.")

        # Alpha Vantage: news/sentiment across all symbols
        news = self.alpha_vantage.news_sentiment(symbols)
        state.research_notes.extend(news)

        # Alpha Vantage: per-symbol earnings + fundamentals
        fundamental_count = 0
        for symbol in symbols:
            earnings = self.alpha_vantage.earnings_summary(symbol)
            overview = self.alpha_vantage.overview_summary(symbol)
            state.research_notes.extend(earnings)
            state.research_notes.extend(overview)
            fundamental_count += len(earnings) + len(overview)

        parts = []
        if news:
            parts.append(f"{len(news)} news item(s)")
        if fundamental_count:
            parts.append(f"{fundamental_count} fundamental data point(s)")
        av_note = f"Alpha Vantage: {', '.join(parts)}." if parts else "Alpha Vantage: rate limit hit — cached data will be used on next run."
        state.agent_outputs["research_curator"] = av_note

    def _run_scenario_cartographer(
        self,
        state: CouncilRunState,
        topic: TopicAnalysis,
        force: bool = False,
    ) -> None:
        if not force and state.simulation_factory.get("status") == "running":
            state.simulation_insights.append(
                "Live MiroFish simulation is still running — moves below update when it finishes."
            )
            return
        if not state.simulation_id:
            return
        try:
            self.mirofish.health()
            insights = self.mirofish.fetch_scenario_insights(state.simulation_id, state.user_question)
            state.simulation_insights = insights or state.simulation_insights
            state.agent_outputs["scenario_cartographer"] = (
                f"Pulled {len(insights)} insight(s) from {state.simulation_id}."
            )
        except (MiroFishError, httpx.HTTPError) as exc:
            state.simulation_insights.append(f"MiroFish unavailable: {exc}")

    def _run_compliance_skeptic(self, state: CouncilRunState, topic: TopicAnalysis) -> None:
        if topic.primary_topic in {"florida_housing", "housing"}:
            state.risk_flags.append(
                "Florida homes can carry hidden costs — flood, wind, and rising insurance."
            )
        state.risk_flags.append(
            "Suggested moves are simulation-informed decision support — not guaranteed returns or regulated advice."
        )

    def _run_scenario_synthesizer(self, state: CouncilRunState, topic: TopicAnalysis) -> None:
        state.scenario_brief = {
            "base": topic.scenario_base,
            "upside": topic.scenario_upside,
            "downside": topic.scenario_downside,
        }
        if state.simulation_insights:
            state.scenario_brief["base"] = (
                f"{topic.scenario_base} Simulation: {state.simulation_insights[0][:220]}"
            )

    def council_manifest(self) -> str:
        lines = ["# Apex Council", "", self.skills.catalog_for_prompt(), ""]
        for role in COUNCIL_ROLES:
            lines.append(f"## {role.title} (`{role.id}`)")
            lines.append(role.mandate)
            lines.append(f"Skill: `{role.skill_name}`")
            lines.append("")
        return "\n".join(lines)

    def keys_status(self) -> dict:
        keys = load_mirofish_keys()
        kronos_ok = False
        try:
            kronos_ok = self.kronos.health().get("status") == "ok"
        except Exception:
            kronos_ok = False
        return {
            "valid": keys.valid,
            "llm_configured": bool(keys.llm_api_key),
            "zep_configured": bool(keys.zep_api_key),
            "kronos": "ok" if kronos_ok else "unreachable",
        }
