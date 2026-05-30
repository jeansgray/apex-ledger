"""Apex Ledger CLI."""

from __future__ import annotations

import argparse
import json
import sys

from .config import get_settings
from .council.graph import CouncilOrchestrator


def main() -> None:
    parser = argparse.ArgumentParser(prog="apex-ledger", description="Apex Ledger council CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    run_parser = sub.add_parser("council-run", help="Run the Apex Council pipeline")
    run_parser.add_argument("question", help="Investor question or scenario prompt")
    run_parser.add_argument("--simulation-id", default=None, help="MiroFish simulation ID")
    run_parser.add_argument("--no-seed", action="store_true", help="Skip demo ledger seed")

    sub.add_parser("council-roster", help="Print council roles and skills")
    sub.add_parser("seed-ledger", help="Seed demo portfolio and transactions")

    serve_parser = sub.add_parser("serve", help="Start FastAPI server")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8080)

    args = parser.parse_args()
    settings = get_settings()
    orchestrator = CouncilOrchestrator(settings)

    if args.command == "council-run":
        state = orchestrator.run(
            user_question=args.question,
            simulation_id=args.simulation_id or settings.mirofish_default_simulation_id or None,
            seed_demo=not args.no_seed,
        )
        print(json.dumps(state.model_dump(mode="json"), indent=2))
        return

    if args.command == "council-roster":
        print(orchestrator.council_manifest())
        return

    if args.command == "seed-ledger":
        orchestrator.ledger.seed_demo_data()
        print(json.dumps(orchestrator.ledger.portfolio_snapshot(), indent=2))
        return

    if args.command == "serve":
        import uvicorn

        uvicorn.run(
            "apex_ledger.api.app:app",
            host=args.host,
            port=args.port,
            reload=True,
        )
        return

    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
