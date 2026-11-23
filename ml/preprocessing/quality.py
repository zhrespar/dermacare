"""Image quality-check contract (blur, exposure, face size, ROI visibility, occlusion).

Thresholds are NOT set yet: per the proposal they are determined on the validation
split and frozen before final testing. Implementation will use OpenCV
(Laplacian variance, histogram statistics) and MediaPipe Face Mesh landmarks.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class QualityStatus(str, Enum):
    ACCEPTED = "accepted"
    RETAKE = "retake"  # fixable: blur, lighting, framing
    OUT_OF_SCOPE = "out_of_scope"  # no face / multiple faces / unusable


@dataclass(frozen=True)
class QualityReport:
    status: QualityStatus
    reasons: list[str]
    blur_score: float | None = None
    brightness: float | None = None
    face_area_ratio: float | None = None
