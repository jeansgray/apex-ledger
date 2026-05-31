"""FinBERT sentiment scorer for financial headlines.

Lazy-loads ProsusAI/finbert on first use (~450MB, cached in ~/.cache/huggingface).
Returns positive / negative / neutral with confidence score.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

_pipeline = None  # lazy singleton


def _get_pipeline():
    global _pipeline
    if _pipeline is None:
        from transformers import pipeline  # noqa: PLC0415

        _pipeline = pipeline(
            "text-classification",
            model="ProsusAI/finbert",
            tokenizer="ProsusAI/finbert",
            device=-1,  # CPU
            top_k=None,  # return all 3 labels
        )
    return _pipeline


class FinBertScorer:
    """Score financial text with FinBERT. Results are disk-cached."""

    def __init__(self, cache_dir: Path | None = None) -> None:
        self.cache_dir = cache_dir or Path.home() / ".cache" / "apex_ledger" / "finbert"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _cache_path(self, text: str) -> Path:
        key = hashlib.md5(text.encode()).hexdigest()
        return self.cache_dir / f"{key}.json"

    def score(self, text: str) -> dict[str, Any]:
        """Return {label, score, scores: {positive, negative, neutral}}."""
        if not text or not text.strip():
            return {"label": "neutral", "score": 0.0, "scores": {"positive": 0.33, "negative": 0.33, "neutral": 0.34}}

        cache_path = self._cache_path(text)
        if cache_path.exists():
            return json.loads(cache_path.read_text())

        try:
            pipe = _get_pipeline()
            # Truncate to 512 tokens max
            results = pipe(text[:512], truncation=True)[0]
            scores = {r["label"].lower(): round(r["score"], 4) for r in results}
            best = max(scores, key=lambda k: scores[k])
            out = {"label": best, "score": round(scores[best], 4), "scores": scores}
            cache_path.write_text(json.dumps(out))
            return out
        except Exception:
            return {"label": "neutral", "score": 0.0, "scores": {"positive": 0.33, "negative": 0.33, "neutral": 0.34}}

    def score_batch(self, texts: list[str]) -> list[dict[str, Any]]:
        """Score a list of texts, using cache where available."""
        return [self.score(t) for t in texts]

    def sentiment_float(self, text: str) -> float:
        """Return a float in [-1, 1]: positive=+1, negative=-1, neutral=0."""
        result = self.score(text)
        s = result.get("scores", {})
        return round(s.get("positive", 0.0) - s.get("negative", 0.0), 4)
