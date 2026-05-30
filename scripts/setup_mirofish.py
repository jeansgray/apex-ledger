#!/usr/bin/env python3
"""Install, configure, seed, and start the MiroFish backend for Apex Ledger."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIROFISH_ROOT = ROOT / "vendor/mirofish"
BACKEND = MIROFISH_ROOT / "backend"
SECRETS_DIR = Path.home() / ".config/apex-ledger"
SECRETS_FILE = SECRETS_DIR / "mirofish.env"
SECRETS_EXAMPLE = SECRETS_DIR / "mirofish.env.example"
MIROFISH_ENV = MIROFISH_ROOT / ".env"
DEFAULT_SIMULATION_ID = "sim_apex_personal_investor"


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    print("+", " ".join(cmd))
    return subprocess.run(cmd, check=True, **kwargs)


def ensure_python312() -> str:
    try:
        run(["uv", "python", "install", "3.12"], cwd=ROOT)
    except subprocess.CalledProcessError:
        pass
    probe = subprocess.run(
        ["uv", "python", "find", "3.12"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if probe.returncode == 0 and probe.stdout.strip():
        return probe.stdout.strip()
    # Fall back to system python — may fail MiroFish constraints
    return sys.executable


def ensure_secrets() -> None:
    SECRETS_DIR.mkdir(parents=True, exist_ok=True)
    if not SECRETS_EXAMPLE.exists():
        shutil.copy(MIROFISH_ROOT / ".env.example", SECRETS_EXAMPLE)
    if not SECRETS_FILE.exists():
        content = (MIROFISH_ROOT / ".env.example").read_text(encoding="utf-8")
        content = content.replace("your_api_key_here", "dev-placeholder-start-only")
        content = content.replace("your_zep_api_key_here", "dev-placeholder-start-only")
        SECRETS_FILE.write_text(content, encoding="utf-8")
        SECRETS_FILE.chmod(0o600)
        print(f"Created {SECRETS_FILE} — add real LLM + Zep keys for live simulations.")

    shutil.copy(SECRETS_FILE, MIROFISH_ENV)


def keys_look_real() -> bool:
    if not SECRETS_FILE.exists():
        return False
    text = SECRETS_FILE.read_text(encoding="utf-8")
    for placeholder in ("your_api_key", "your_zep", "dev-placeholder-start-only", "REPLACE_WITH"):
        if placeholder in text:
            return False
    return "LLM_API_KEY=" in text and "ZEP_API_KEY=" in text


def sync_backend(python: str) -> None:
    run(["uv", "sync"], cwd=BACKEND, env={**os.environ, "UV_PYTHON": python})


def seed_fixture() -> str:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/seed_personal_investor_simulation.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip() or DEFAULT_SIMULATION_ID


def update_apex_env(simulation_id: str) -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        shutil.copy(ROOT / ".env.example", env_path)
    lines = env_path.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    seen_sim = False
    seen_url = False
    for line in lines:
        if line.startswith("MIROFISH_DEFAULT_SIMULATION_ID="):
            out.append(f"MIROFISH_DEFAULT_SIMULATION_ID={simulation_id}")
            seen_sim = True
        elif line.startswith("MIROFISH_BASE_URL="):
            out.append("MIROFISH_BASE_URL=http://127.0.0.1:5001")
            seen_url = True
        else:
            out.append(line)
    if not seen_sim:
        out.append(f"MIROFISH_DEFAULT_SIMULATION_ID={simulation_id}")
    if not seen_url:
        out.append("MIROFISH_BASE_URL=http://127.0.0.1:5001")
    env_path.write_text("\n".join(out) + "\n", encoding="utf-8")


def start_backend(python: str, background: bool) -> subprocess.Popen | None:
    env = os.environ.copy()
    env["UV_PYTHON"] = python
    cmd = ["uv", "run", "python", "run.py"]
    if background:
        proc = subprocess.Popen(
            cmd,
            cwd=BACKEND,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        for _ in range(30):
            time.sleep(0.5)
            try:
                import httpx

                r = httpx.get("http://127.0.0.1:5001/health", timeout=1.0)
                if r.status_code == 200:
                    print("MiroFish backend is up on http://127.0.0.1:5001")
                    return proc
            except Exception:
                if proc.poll() is not None:
                    out = proc.stdout.read() if proc.stdout else ""
                    raise RuntimeError(f"MiroFish exited early:\n{out}")
        raise TimeoutError("MiroFish did not become healthy within 15s")
    run(cmd, cwd=BACKEND, env=env)
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--foreground", action="store_true", help="Run MiroFish in foreground")
    parser.add_argument("--no-start", action="store_true", help="Configure only, do not start server")
    args = parser.parse_args()

    python = ensure_python312()
    ensure_secrets()
    sync_backend(python)
    simulation_id = seed_fixture()
    update_apex_env(simulation_id)
    print(f"Seeded simulation fixture: {simulation_id}")

    if keys_look_real():
        print("Real API keys detected — you can run scripts/bootstrap_personal_investor_simulation.py")
    else:
        print(
            "Using seeded fixture (read-only MiroFish APIs). "
            f"Add keys to {SECRETS_FILE} for live simulations."
        )

    if args.no_start:
        return

    start_backend(python, background=not args.foreground)


if __name__ == "__main__":
    main()
