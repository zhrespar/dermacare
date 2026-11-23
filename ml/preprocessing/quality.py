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


@dataclass(frozen=True)
class QualityMetrics:
    """Measured by `compute_metrics` (OpenCV) + a face detector. None = not measured."""

    face_count: int
    blur_score: float | None = None  # variance of Laplacian on the face crop
    brightness: float | None = None  # mean gray level 0..255
    face_area_ratio: float | None = None  # face box area / image area
    roi_visible: bool | None = None  # cheeks + under-eye regions inside frame and unoccluded


@dataclass(frozen=True)
class QualityThresholds:
    """PROVISIONAL development values — to be tuned on the validation split and frozen."""

    min_blur: float = 60.0
    min_brightness: float = 50.0
    max_brightness: float = 215.0
    min_face_area_ratio: float = 0.12
    version: str = "0.1.0-provisional"


DEFAULT_QUALITY_THRESHOLDS = QualityThresholds()


def decide_quality(m: QualityMetrics, t: QualityThresholds = DEFAULT_QUALITY_THRESHOLDS) -> QualityReport:
    if m.face_count == 0:
        return QualityReport(QualityStatus.OUT_OF_SCOPE, ["no_face_detected"])
    if m.face_count > 1:
        return QualityReport(QualityStatus.OUT_OF_SCOPE, ["multiple_faces"])
    reasons: list[str] = []
    if m.blur_score is not None and m.blur_score < t.min_blur:
        reasons.append("blurry")
    if m.brightness is not None and m.brightness < t.min_brightness:
        reasons.append("too_dark")
    if m.brightness is not None and m.brightness > t.max_brightness:
        reasons.append("overexposed")
    if m.face_area_ratio is not None and m.face_area_ratio < t.min_face_area_ratio:
        reasons.append("face_too_small")
    if m.roi_visible is False:
        reasons.append("regions_not_visible")
    status = QualityStatus.RETAKE if reasons else QualityStatus.ACCEPTED
    return QualityReport(status, reasons, m.blur_score, m.brightness, m.face_area_ratio)


def compute_metrics(image_bgr, face_box: tuple[int, int, int, int] | None, face_count: int) -> QualityMetrics:
    """OpenCV measurement (requires ml/requirements.txt). face_box in pixels (x0, y0, x1, y1)."""
    import cv2  # lazy: backend/mock path must not need OpenCV

    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape[:2]
    if face_box is None:
        return QualityMetrics(face_count=face_count, brightness=float(gray.mean()))
    x0, y0, x1, y1 = face_box
    crop = gray[y0:y1, x0:x1]
    return QualityMetrics(
        face_count=face_count,
        blur_score=float(cv2.Laplacian(crop, cv2.CV_64F).var()),
        brightness=float(crop.mean()),
        face_area_ratio=((x1 - x0) * (y1 - y0)) / float(w * h),
    )
