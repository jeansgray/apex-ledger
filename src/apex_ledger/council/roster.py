"""Apex Council — agent roles for personal investors."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CouncilRole:
    id: str
    title: str
    mandate: str
    skill_name: str
    runs_after: tuple[str, ...] = ()


COUNCIL_ROLES: tuple[CouncilRole, ...] = (
    CouncilRole(
        id="ledger_steward",
        title="Ledger Steward",
        mandate=(
            "Load holdings, cash, and unmatched transactions. "
            "Surface reconciliation candidates with evidence."
        ),
        skill_name="apex-ledger-read",
    ),
    CouncilRole(
        id="research_curator",
        title="Research Curator",
        mandate=(
            "Gather macro and issuer context relevant to the user's question "
            "and portfolio exposures."
        ),
        skill_name="apex-research-curator",
        runs_after=("ledger_steward",),
    ),
    CouncilRole(
        id="quant_forecaster",
        title="Quant Forecaster",
        mandate=(
            "Run Kronos-style OHLCV forecasts on portfolio symbols; summarize direction, "
            "return path, and volatility for the council."
        ),
        skill_name="apex-quant-forecast",
        runs_after=("ledger_steward",),
    ),
    CouncilRole(
        id="scenario_cartographer",
        title="Scenario Cartographer",
        mandate=(
            "Use MiroFish simulation outputs (interviews, timeline, report) "
            "to map base, upside, and downside futures."
        ),
        skill_name="apex-scenario-brief",
        runs_after=("ledger_steward", "research_curator"),
    ),
    CouncilRole(
        id="compliance_skeptic",
        title="Compliance Skeptic",
        mandate=(
            "Challenge concentration, liquidity, and assumption risk "
            "for a personal investor — not institutional compliance."
        ),
        skill_name="apex-risk-check",
        runs_after=("scenario_cartographer",),
    ),
    CouncilRole(
        id="scenario_synthesizer",
        title="Scenario Synthesizer",
        mandate=(
            "Merge ledger state, research, simulation, and risk review "
            "into an actionable brief with explicit human-approval gates."
        ),
        skill_name="apex-council-synthesis",
        runs_after=("compliance_skeptic",),
    ),
    CouncilRole(
        id="reconciliation_proposer",
        title="Reconciliation Proposer",
        mandate=(
            "Propose category matches for unmatched transactions; "
            "never post to the ledger without human approval."
        ),
        skill_name="apex-reconciliation",
        runs_after=("ledger_steward",),
    ),
)


def role_by_id(role_id: str) -> CouncilRole:
    for role in COUNCIL_ROLES:
        if role.id == role_id:
            return role
    raise KeyError(f"Unknown council role: {role_id}")
