"""Pure-Python ML utilities on toy data (no datasets, no torch)."""

import pytest

from ml.evaluation import metrics as M
from ml.preprocessing.face_regions import REGIONS, assign_region, canonical_regions
from ml.preprocessing.quality import QualityMetrics, QualityStatus, decide_quality
from ml.training.configs import ALL_CONFIGS


def test_canonical_regions_cover_expected_names_and_assign():
    regs = canonical_regions()
    assert {r.name for r in regs} == set(REGIONS)
    assert assign_region(0.45, 0.15, 0.55, 0.2, regs) == "forehead"
    assert assign_region(0.2, 0.55, 0.25, 0.6, regs) == "right_cheek"
    assert assign_region(0.0, 0.0, 0.01, 0.01, regs) is None


@pytest.mark.parametrize(
    "m,status,reason",
    [
        (QualityMetrics(face_count=0), QualityStatus.OUT_OF_SCOPE, "no_face_detected"),
        (QualityMetrics(face_count=2), QualityStatus.OUT_OF_SCOPE, "multiple_faces"),
        (QualityMetrics(face_count=1, blur_score=10), QualityStatus.RETAKE, "blurry"),
        (QualityMetrics(face_count=1, brightness=20), QualityStatus.RETAKE, "too_dark"),
        (QualityMetrics(face_count=1, face_area_ratio=0.01), QualityStatus.RETAKE, "face_too_small"),
    ],
)
def test_quality_decisions(m, status, reason):
    r = decide_quality(m)
    assert r.status == status and reason in r.reasons


def test_quality_accepts_good_image():
    r = decide_quality(
        QualityMetrics(1, blur_score=200, brightness=120, face_area_ratio=0.3, roi_visible=True)
    )
    assert r.status == QualityStatus.ACCEPTED and r.reasons == []


def test_metrics_on_toy_arrays():
    assert M.iou((0, 0, 2, 2), (1, 1, 3, 3)) == pytest.approx(1 / 7)
    assert M.dice_iou_binary([1, 1, 0, 0], [1, 0, 1, 0]) == (0.5, pytest.approx(1 / 3))
    assert M.macro_f1([0, 1, 2, 3], [0, 1, 2, 3], 4) == 1.0
    assert M.quadratic_weighted_kappa([0, 1, 2, 3], [0, 1, 2, 3], 4) == pytest.approx(1.0)
    assert M.binary_f1([1, 0, 1, 1], [1, 0, 0, 1]) == pytest.approx(0.8)
    assert M.roc_auc([0, 0, 1, 1], [0.1, 0.4, 0.35, 0.8]) == 0.75


def test_average_precision_perfect_and_miss():
    gts = {"a": [(0, 0, 1, 1)], "b": [(0, 0, 1, 1)]}
    assert M.average_precision([("a", 0.9, (0, 0, 1, 1)), ("b", 0.8, (0, 0, 1, 1))], gts) == 1.0
    assert M.average_precision([("a", 0.9, (0, 0, 1, 1))], gts) == 0.5


def test_train_configs_use_pretrained_and_noncommercial_flags():
    assert set(ALL_CONFIGS) == {
        "acne_detection",
        "acne_severity",
        "wrinkle_segmentation",
        "under_eye_classification",
    }
    for c in ALL_CONFIGS.values():
        assert c.pretrained_on and c.candidates and c.dataset.commercial_use is False
