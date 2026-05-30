#!/usr/bin/env python3
"""Configure MiroFish LLM + Zep keys for Apex Ledger."""

from __future__ import annotations

import os
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECRETS = Path.home() / ".config" / "apex-ledger"
MIROFISH_ENV = SECRETS / "mirofish.env"
VENDOR_ENV = ROOT / "vendor" / "mirofish" / ".env"
APEX_ENV = ROOT / ".env"
EXAMPLE = ROOT / "vendor" / "mirofish" / ".env.example"


def _read_env(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.strip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        out[key.strip()] = value.strip()
    return out


def _upsert_env(path: Path, updates: dict[str, str]) -> None:
    lines: list[str] = []
    if path.exists():
        lines = path.read_text(encoding="utf-8").splitlines()
    remaining = set(updates)
    out: list[str] = []
    for line in lines:
        if "=" in line and not line.strip().startswith("#"):
            key = line.split("=", 1)[0].strip()
            if key in updates:
                out.append(f"{key}={updates[key]}")
                remaining.discard(key)
                continue
        out.append(line)
    for key in sorted(remaining):
        out.append(f"{key}={updates[key]}")
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def main() -> None:
    SECRETS.mkdir(parents=True, exist_ok=True)
    apex = _read_env(APEX_ENV)
    merged = _read_env(MIROFISH_ENV)

    llm = (
        os.environ.get("LLM_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or apex.get("LLM_API_KEY")
        or merged.get("LLM_API_KEY")
        or ""
    )
    zep = os.environ.get("ZEP_API_KEY") or apex.get("ZEP_API_KEY") or merged.get("ZEP_API_KEY") or ""
    base = apex.get("LLM_BASE_URL") or merged.get("LLM_BASE_URL") or "https://api.openai.com/v1"
    model = apex.get("LLM_MODEL_NAME") or merged.get("LLM_MODEL_NAME") or "gpt-4o-mini"

    if not llm or not zep or "placeholder" in llm.lower() or "placeholder" in zep.lower():
        print("Missing real API keys.", file=sys.stderr)
        print("Add to .env or export in shell:", file=sys.stderr)
        print("  LLM_API_KEY=sk-...", file=sys.stderr)
        print("  ZEP_API_KEY=...", file=sys.stderr)
        print(f"Then run: python3 {Path(__file__).name}", file=sys.stderr)
        if not MIROFISH_ENV.exists() and EXAMPLE.exists():
            shutil.copy(EXAMPLE, MIROFISH_ENV)
            MIROFISH_ENV.chmod(0o600)
        sys.exit(1)

    if EXAMPLE.exists():
        content = EXAMPLE.read_text(encoding="utf-8")
        content = re.sub(r"^LLM_API_KEY=.*$", f"LLM_API_KEY={llm}", content, flags=re.M)
        content = re.sub(r"^ZEP_API_KEY=.*$", f"ZEP_API_KEY={zep}", content, flags=re.M)
        content = re.sub(r"^LLM_BASE_URL=.*$", f"LLM_BASE_URL={base}", content, flags=re.M)
        content = re.sub(r"^LLM_MODEL_NAME=.*$", f"LLM_MODEL_NAME={model}", content, flags=re.M)
        content = re.sub(r"^LLM_BOOST_.*\n", "", content, flags=re.M)
        MIROFISH_ENV.write_text(content, encoding="utf-8")
    else:
        MIROFISH_ENV.write_text(
            f"LLM_API_KEY={llm}\nZEP_API_KEY={zep}\nLLM_BASE_URL={base}\nLLM_MODEL_NAME={model}\n",
            encoding="utf-8",
        )
    MIROFISH_ENV.chmod(0o600)
    shutil.copy(MIROFISH_ENV, VENDOR_ENV)
    _upsert_env(
        APEX_ENV,
        {
            "LLM_API_KEY": llm,
            "ZEP_API_KEY": zep,
            "LLM_BASE_URL": base,
            "LLM_MODEL_NAME": model,
        },
    )
    print(f"Keys configured in {MIROFISH_ENV}")
    print("Restart: MiroFish backend (:5001) and apex-ledger serve (:8080)")


if __name__ == "__main__":
    main()
