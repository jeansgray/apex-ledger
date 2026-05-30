"""Build client-safe friendly brief JSON (also used to verify API responses)."""

from __future__ import annotations

from .presentation import build_friendly_brief
from .state import CouncilRunState
from .topics import analyze_question


def ensure_friendly_brief(state: CouncilRunState) -> dict:
    if state.friendly_brief:
        return state.friendly_brief
    topic = analyze_question(state.user_question)
    if not state.topic_analysis:
        state.topic_analysis = {
            "primary_topic": topic.primary_topic,
            "topic_label": topic.topic_label,
            "direct_answer": topic.direct_answer,
        }
    return build_friendly_brief(state, topic).model_dump()
