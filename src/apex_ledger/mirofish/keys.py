"""MiroFish API key discovery (reads ~/.config/apex-ledger/mirofish.env)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values

MIROFISH_ENV = Path.home() / ".config" / "apex-ledger" / "mirofish.env"
VENDOR_ENV = Path(__file__).resolve().parents[3] / "vendor" / "mirofish" / ".env"
PLACEHOLDERS = ("dev-placeholder", "your_api_key", "your_zep", "REPLACE_WITH", "your_base_url")


@dataclass
class MiroFishKeys:
    llm_api_key: str
    zep_api_key: str
    llm_base_url: str
    llm_model_name: str

    @property
    def valid(self) -> bool:
        if not self.llm_api_key or not self.zep_api_key:
            return False
        combined = f"{self.llm_api_key} {self.zep_api_key}".lower()
        return not any(p in combined for p in PLACEHOLDERS)


def load_mirofish_keys() -> MiroFishKeys:
    merged: dict[str, str | None] = {}
    for path in (MIROFISH_ENV, VENDOR_ENV, Path(".env")):
        if path.exists():
            merged.update({k: v for k, v in dotenv_values(path).items() if v})

    llm = (
        os.environ.get("LLM_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or merged.get("LLM_API_KEY")
        or ""
    )
    zep = os.environ.get("ZEP_API_KEY") or merged.get("ZEP_API_KEY") or ""
    return MiroFishKeys(
        llm_api_key=llm.strip(),
        zep_api_key=zep.strip(),
        llm_base_url=(merged.get("LLM_BASE_URL") or "https://api.openai.com/v1").strip(),
        llm_model_name=(merged.get("LLM_MODEL_NAME") or "gpt-4o-mini").strip(),
    )
