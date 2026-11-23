"""MOCK ANALYSIS SERVICE — wires placeholder models through the real pipeline shape.

Outputs are flagged `is_mock=True` and must never be shown as real results.
Image bytes are not persisted. Swap `ANALYSIS_BACKEND=torch` once trained models
implement ml.inference.interfaces.
"""

from __future__ import annotations

import hashlib
import uuid
from collections import Counter

from app.schemas.analysis import (
    AcneOut,
    AnalysisResponse,
    BoxOut,
    QualityOut,
    RegionSummary,
    UnderEyeOut,
    WrinkleOut,
)
from app.services.analysis.triage import DEFAULT_THRESHOLDS, triage
from ml.inference.interfaces import ImageInput
from ml.inference.mock_models import MockAcneDetector, MockUnderEyeClassifier, MockWrinkleSegmenter
from ml.preprocessing.face_regions import assign_region, canonical_regions

DISCLAIMER = (
    "DermaCare is a cosmetic decision-support research prototype. It does not diagnose or "
    "treat any disease. Consult a dermatologist for medical concerns."
)
SEVERITY = ["mild", "moderate", "severe", "very_severe"]
JPEG_MAGIC = b"\xff\xd8\xff"
PNG_MAGIC = b"\x89PNG"


def basic_quality_check(data: bytes) -> QualityOut:
    """Upload gate: format/size only. Real checks: ml.preprocessing.quality.decide_quality."""
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
            triage=triage(quality, None, None, None),
            acne=None,
            wrinkles=None,
            under_eye=None,
            model_versions={},
            thresholds_version=DEFAULT_THRESHOLDS.version,
            disclaimer=DISCLAIMER,
        )

    img = ImageInput(image_bytes=data, width=0, height=0)
    a = MockAcneDetector().predict(img)
    w = MockWrinkleSegmenter().predict(img)
    u = MockUnderEyeClassifier().predict(img)
    regions = canonical_regions()
    boxes = [
        BoxOut(**b.__dict__, region=assign_region(b.x_min, b.y_min, b.x_max, b.y_max, regions))
        for b in a.lesions
    ]
    acne = AcneOut(
        lesion_count=a.lesion_count,
        lesions=boxes,
        severity=SEVERITY[a.severity],
        severity_probabilities=a.severity_probabilities,
    )
    wrinkles = WrinkleOut(affected_area_ratio=w.affected_area_ratio, mean_confidence=w.mean_confidence)
    under_eye = UnderEyeOut(present=u.present, probability=u.probability)
    t = triage(quality, acne, wrinkles, under_eye)
    t.reasons.append("mock_backend")
    counts = Counter(b.region for b in boxes if b.region)
    return AnalysisResponse(
        id=aid,
        is_mock=True,
        quality=quality,
        triage=t,
        acne=acne,
        wrinkles=wrinkles,
        under_eye=under_eye,
        regions=[RegionSummary(region=r, lesion_count=c) for r, c in sorted(counts.items())],
        model_versions={"acne": a.model_version, "wrinkles": w.model_version, "under_eye": u.model_version},
        thresholds_version=DEFAULT_THRESHOLDS.version,
        disclaimer=DISCLAIMER,
    )
