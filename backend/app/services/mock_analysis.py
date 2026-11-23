"""MOCK ANALYSIS SERVICE — wires placeholder models through the real pipeline shape.

Outputs are flagged `is_mock=True` and must never be shown as real results.
Swap `analysis_backend=torch` once trained models implement ml.inference.interfaces.
"""

from __future__ import annotations

import hashlib
import uuid

from app.schemas.analysis import (
    AcneOut,
    AnalysisResponse,
    BoxOut,
    QualityOut,
    TriageOut,
    UnderEyeOut,
    WrinkleOut,
)
from ml.inference.interfaces import ImageInput
from ml.inference.mock_models import MockAcneDetector, MockUnderEyeClassifier, MockWrinkleSegmenter

DISCLAIMER = (
    "DermaCare is a cosmetic decision-support research prototype. It does not diagnose or "
    "treat any disease. Consult a dermatologist for medical concerns."
)
_SEVERITY = ["mild", "moderate", "severe", "very_severe"]
JPEG_MAGIC = b"\xff\xd8\xff"
PNG_MAGIC = b"\x89PNG"


def basic_quality_check(data: bytes) -> QualityOut:
    """Placeholder: format/size only. See ml/preprocessing for the real check."""
    if not (data.startswith(JPEG_MAGIC) or data.startswith(PNG_MAGIC)):
        return QualityOut(status="out_of_scope", reasons=["unsupported_format"])
    if len(data) < 1024:
        return QualityOut(status="retake", reasons=["image_too_small"])
    return QualityOut(status="accepted", reasons=[])


def run_mock_analysis(data: bytes) -> AnalysisResponse:
    quality = basic_quality_check(data)
    aid = str(uuid.UUID(hashlib.sha256(data).hexdigest()[:32]))
    if quality.status != "accepted":
        return AnalysisResponse(
            id=aid,
            is_mock=True,
            quality=quality,
            triage=TriageOut(action="retake", reasons=quality.reasons),
            acne=None,
            wrinkles=None,
            under_eye=None,
            model_versions={},
            disclaimer=DISCLAIMER,
        )

    img = ImageInput(image_bytes=data, width=0, height=0)
    acne = MockAcneDetector().predict(img)
    wr = MockWrinkleSegmenter().predict(img)
    ue = MockUnderEyeClassifier().predict(img)
    return AnalysisResponse(
        id=aid,
        is_mock=True,
        quality=quality,
        triage=TriageOut(action="proceed", reasons=["mock_backend"]),
        acne=AcneOut(
            lesion_count=acne.lesion_count,
            lesions=[BoxOut(**b.__dict__) for b in acne.lesions],
            severity=_SEVERITY[acne.severity],
            severity_probabilities=acne.severity_probabilities,
        ),
        wrinkles=WrinkleOut(affected_area_ratio=wr.affected_area_ratio, mean_confidence=wr.mean_confidence),
        under_eye=UnderEyeOut(present=ue.present, probability=ue.probability),
        model_versions={
            "acne": acne.model_version,
            "wrinkles": wr.model_version,
            "under_eye": ue.model_version,
        },
        disclaimer=DISCLAIMER,
    )
