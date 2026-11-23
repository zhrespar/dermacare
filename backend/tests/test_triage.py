from app.schemas.analysis import AcneOut, QualityOut, UnderEyeOut, WrinkleOut
from app.services.analysis.triage import triage

OK = QualityOut(status="accepted", reasons=[])


def _acne(sev="mild", probs=(0.7, 0.1, 0.1, 0.1)):
    return AcneOut(lesion_count=0, lesions=[], severity=sev, severity_probabilities=list(probs))


def test_poor_quality_retake_and_out_of_scope():
    assert triage(QualityOut(status="retake", reasons=["blurry"]), None, None, None).action == "retake"
    t = triage(QualityOut(status="out_of_scope", reasons=["no_face_detected"]), None, None, None)
    assert t.action == "retake" and "image_out_of_scope" in t.reasons


def test_very_severe_refers():
    t = triage(OK, _acne("very_severe", (0.1, 0.1, 0.1, 0.7)), None, None)
    assert t.action == "refer_dermatologist"


def test_low_confidence_limits():
    t = triage(
        OK,
        _acne(probs=(0.3, 0.3, 0.2, 0.2)),
        WrinkleOut(affected_area_ratio=0.1, mean_confidence=0.2),
        UnderEyeOut(present=True, probability=0.5),
    )
    assert t.action == "limited"
    assert set(t.reasons) == {"low_confidence_acne", "low_confidence_wrinkles", "uncertain_under_eye"}


def test_confident_proceeds():
    t = triage(
        OK,
        _acne(),
        WrinkleOut(affected_area_ratio=0.1, mean_confidence=0.8),
        UnderEyeOut(present=False, probability=0.1),
    )
    assert t.action == "proceed" and t.reasons == []
