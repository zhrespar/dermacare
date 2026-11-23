"""CV analysis service: quality gate -> 3 task models -> region mapping -> triage.

Backends:
  mock  -> labelled placeholder models (is_mock=True). Default.
  torch -> trained models implementing ml.inference.interfaces (not available yet).
"""

from __future__ import annotations

from app.schemas.analysis import AnalysisResponse
from app.services.analysis.mock import DISCLAIMER, basic_quality_check, run_mock_analysis


class AnalysisBackendUnavailable(RuntimeError):
    pass


def run_analysis(data: bytes, backend: str) -> AnalysisResponse:
    if backend == "mock":
        return run_mock_analysis(data)
    # Real inference stays separate from mock/demo code; it will load versioned weights
    # registered in ML_EXPERIMENTS.md. No trained weights exist yet.
    raise AnalysisBackendUnavailable(f"analysis backend '{backend}' has no registered models")


__all__ = ["DISCLAIMER", "AnalysisBackendUnavailable", "basic_quality_check", "run_analysis"]
