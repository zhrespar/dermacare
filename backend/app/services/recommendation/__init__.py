"""Deterministic, auditable recommendation pipeline (no trained model, no LLM)."""

from app.services.recommendation.engine import derive_needs, recommend
from app.services.recommendation.routine import build_routine
from app.services.recommendation.rules import RULES_VERSION

__all__ = ["RULES_VERSION", "build_routine", "derive_needs", "recommend"]
