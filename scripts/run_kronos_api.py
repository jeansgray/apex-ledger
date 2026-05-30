#!/usr/bin/env python3
"""Run the Kronos forecast API locally."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQ = ROOT / "services/kronos_api/requirements.txt"


def main() -> None:
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-q", "-r", str(REQ)],
    )
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "services.kronos_api.app:app",
            "--host",
            "127.0.0.1",
            "--port",
            "5002",
            "--reload",
        ],
        cwd=ROOT,
    )


if __name__ == "__main__":
    main()
