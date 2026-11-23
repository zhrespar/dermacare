"""Facial region mapping for explainable, region-level outputs.

Regions are derived from five named keypoints (normalized 0..1 image coords), which any
landmark model can supply (e.g. MediaPipe Face Mesh / Face Landmarker indices mapped to
these names in the inference adapter). Pure Python: no cv2/mediapipe import here.

`canonical_regions()` is a fixed frontal-face layout used ONLY by the mock pipeline and tests.
"""

from __future__ import annotations

from dataclasses import dataclass

REGIONS = ("forehead", "left_cheek", "right_cheek", "nose", "chin", "left_under_eye", "right_under_eye")


@dataclass(frozen=True)
class Keypoints:
    left_eye: tuple[float, float]  # subject's left eye (image right when not mirrored)
    right_eye: tuple[float, float]
    nose_tip: tuple[float, float]
    mouth_center: tuple[float, float]
    face_box: tuple[float, float, float, float]  # x_min, y_min, x_max, y_max


@dataclass(frozen=True)
class Region:
    name: str
    x_min: float
    y_min: float
    x_max: float
    y_max: float

    def contains(self, x: float, y: float) -> bool:
        return self.x_min <= x <= self.x_max and self.y_min <= y <= self.y_max


def _clip(v: float) -> float:
    return max(0.0, min(1.0, v))


def regions_from_keypoints(k: Keypoints) -> list[Region]:
    fx0, fy0, fx1, fy1 = k.face_box
    eye_y = (k.left_eye[1] + k.right_eye[1]) / 2
    eye_dx = abs(k.left_eye[0] - k.right_eye[0])
    ue_h = 0.35 * eye_dx  # under-eye band height, proportional to inter-ocular distance
    ue_w = 0.45 * eye_dx
    xs = sorted([k.left_eye, k.right_eye])  # image-left first
    img_left_eye, img_right_eye = xs
    nose_x = k.nose_tip[0]
    raw = [
        ("forehead", fx0, fy0, fx1, eye_y - 0.6 * ue_h),
        ("right_under_eye", img_left_eye[0] - ue_w, eye_y + 0.2 * ue_h, img_left_eye[0] + ue_w, eye_y + ue_h),
        (
            "left_under_eye",
            img_right_eye[0] - ue_w,
            eye_y + 0.2 * ue_h,
            img_right_eye[0] + ue_w,
            eye_y + ue_h,
        ),
        ("nose", nose_x - 0.25 * eye_dx, eye_y + ue_h, nose_x + 0.25 * eye_dx, k.nose_tip[1]),
        ("right_cheek", fx0, eye_y + ue_h, nose_x - 0.25 * eye_dx, k.mouth_center[1]),
        ("left_cheek", nose_x + 0.25 * eye_dx, eye_y + ue_h, fx1, k.mouth_center[1]),
        ("chin", fx0 + 0.25 * (fx1 - fx0), k.mouth_center[1], fx1 - 0.25 * (fx1 - fx0), fy1),
    ]
    return [Region(n, _clip(a), _clip(b), _clip(c), _clip(d)) for n, a, b, c, d in raw if c > a and d > b]


def canonical_regions() -> list[Region]:
    """Fixed layout for MOCK outputs and tests only."""
    return regions_from_keypoints(
        Keypoints(
            left_eye=(0.65, 0.40),
            right_eye=(0.35, 0.40),
            nose_tip=(0.50, 0.58),
            mouth_center=(0.50, 0.72),
            face_box=(0.15, 0.10, 0.85, 0.92),
        )
    )


def assign_region(
    x_min: float, y_min: float, x_max: float, y_max: float, regions: list[Region]
) -> str | None:
    cx, cy = (x_min + x_max) / 2, (y_min + y_max) / 2
    for r in regions:
        if r.contains(cx, cy):
            return r.name
    return None
