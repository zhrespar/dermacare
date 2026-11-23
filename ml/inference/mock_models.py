"""MOCK MODELS — deterministic placeholders. NOT trained, NOT real predictions.

Used only so the end-to-end API and mobile flow can be developed before trained
models exist. Every result carries model_version="mock-0" so it can never be
mistaken for a real model output.
"""

from __future__ import annotations

import hashlib

from ml.inference.interfaces import (
    AcneResult,
    AcneSeverity,
    BoundingBox,
    ImageInput,
    UnderEyeResult,
    WrinkleResult,
)

MOCK_VERSION = "mock-0"


def _seed(image: ImageInput) -> int:
    return int(hashlib.sha256(image.image_bytes).hexdigest()[:8], 16)


class MockAcneDetector:
    def predict(self, image: ImageInput) -> AcneResult:
        s = _seed(image)
        n = s % 4
        boxes = [BoundingBox(0.2 + 0.1 * i, 0.4, 0.25 + 0.1 * i, 0.45, 0.5) for i in range(n)]
        return AcneResult(
            lesions=boxes,
            severity=AcneSeverity(min(n, 3)),
            severity_probabilities=[0.25, 0.25, 0.25, 0.25],
            model_version=MOCK_VERSION,
        )


class MockWrinkleSegmenter:
    def predict(self, image: ImageInput) -> WrinkleResult:
        return WrinkleResult(
            mask_uri=None,
            affected_area_ratio=(_seed(image) % 10) / 100,
            mean_confidence=0.5,
            model_version=MOCK_VERSION,
        )


class MockUnderEyeClassifier:
    def predict(self, image: ImageInput) -> UnderEyeResult:
        return UnderEyeResult(
            present=_seed(image) % 2 == 1,
            probability=0.5,
            gradcam_uri=None,
            model_version=MOCK_VERSION,
        )
