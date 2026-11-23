"""Model-agnostic contracts for the three DermaCare computer-vision tasks.

These interfaces carry no framework dependency (no torch / cv2 import) so the
backend, tests and mock services can use them without the ML stack installed.
Concrete PyTorch implementations live next to this file once models are trained.

Scope (from the TÜBİTAK 2209-B proposal):
  1. Acne     -> lesion detection (bounding boxes) + image-level 4-level severity (ACNE04)
  2. Wrinkles -> pixel-level binary segmentation (FFHQ-Wrinkle)
  3. Under-eye bags -> binary classification (CelebA `Bags_Under_Eyes` attribute)

The under-eye label is a binary facial attribute, NOT a medical severity measure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Protocol, runtime_checkable


class AcneSeverity(IntEnum):
    """ACNE04 image-level grading (Hayashi criterion, 4 levels)."""

    MILD = 0
    MODERATE = 1
    SEVERE = 2
    VERY_SEVERE = 3


@dataclass(frozen=True)
class BoundingBox:
    """Box in normalized image coordinates (0..1)."""

    x_min: float
    y_min: float
    x_max: float
    y_max: float
    confidence: float

    def __post_init__(self) -> None:
        for v in (self.x_min, self.y_min, self.x_max, self.y_max, self.confidence):
            if not 0.0 <= v <= 1.0:
                raise ValueError("BoundingBox values must be within [0, 1]")
        if self.x_min >= self.x_max or self.y_min >= self.y_max:
            raise ValueError("BoundingBox min must be < max")


@dataclass(frozen=True)
class AcneResult:
    lesions: list[BoundingBox]
    severity: AcneSeverity
    severity_probabilities: list[float]  # len 4, sums to ~1
    model_version: str

    @property
    def lesion_count(self) -> int:
        return len(self.lesions)


@dataclass(frozen=True)
class WrinkleResult:
    # Run-length or PNG-encoded mask reference; raw arrays never leave the inference layer.
    mask_uri: str | None
    affected_area_ratio: float  # fraction of the analysed skin ROI predicted as wrinkle
    mean_confidence: float
    model_version: str


@dataclass(frozen=True)
class UnderEyeResult:
    present: bool
    probability: float
    gradcam_uri: str | None
    model_version: str


@dataclass(frozen=True)
class ImageInput:
    """Pre-processed face image handed to models (after quality check + ROI extraction)."""

    image_bytes: bytes
    width: int
    height: int
    rois: dict[str, tuple[int, int, int, int]] = field(default_factory=dict)


@runtime_checkable
class AcneDetector(Protocol):
    def predict(self, image: ImageInput) -> AcneResult: ...


@runtime_checkable
class WrinkleSegmenter(Protocol):
    def predict(self, image: ImageInput) -> WrinkleResult: ...


@runtime_checkable
class UnderEyeClassifier(Protocol):
    def predict(self, image: ImageInput) -> UnderEyeResult: ...
