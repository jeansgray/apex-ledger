"""Persist integration tokens locally (gitignored data dir)."""

from __future__ import annotations

import json
import secrets
from pathlib import Path
from typing import Any


class IntegrationStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _save(self, data: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def get_plaid(self) -> dict[str, Any] | None:
        return self._load().get("plaid")

    def set_plaid(self, access_token: str, item_id: str, institution: str = "") -> None:
        data = self._load()
        data["plaid"] = {
            "access_token": access_token,
            "item_id": item_id,
            "institution": institution,
        }
        self._save(data)

    def clear_plaid(self) -> None:
        data = self._load()
        data.pop("plaid", None)
        self._save(data)

    def get_schwab(self) -> dict[str, Any] | None:
        return self._load().get("schwab")

    def set_schwab(self, tokens: dict[str, Any]) -> None:
        data = self._load()
        data["schwab"] = tokens
        self._save(data)

    def clear_schwab(self) -> None:
        data = self._load()
        data.pop("schwab", None)
        self._save(data)

    def create_oauth_state(self, provider: str) -> str:
        state = secrets.token_urlsafe(24)
        data = self._load()
        data.setdefault("oauth_states", {})[state] = provider
        self._save(data)
        return state

    def consume_oauth_state(self, state: str, provider: str) -> bool:
        data = self._load()
        states = data.get("oauth_states", {})
        if states.get(state) != provider:
            return False
        states.pop(state, None)
        data["oauth_states"] = states
        self._save(data)
        return True
