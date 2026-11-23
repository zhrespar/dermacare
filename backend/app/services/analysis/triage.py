"""Abstention / escalation layer for CV findings.

Maps image quality + model confidence + scope to one action:
  retake              -> unusable image (blur, lighting, no/multiple faces, wrong format)
  limited             -> low confidence: show only profile-based guidance, no CV-driven needs
  refer_dermatologist -> out-of-scope or severe finding: stop cosmetic flow, suggest a dermatologist
  proceed             -> findings may drive recommendations

Thresholds are PROVISIONAL. Per the proposal they are set on the validation split and
frozen before the final test; they are not evidence of clinical performance.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.schemas.analysis import AcneOut, QualityOut, TriageOut, UnderEyeOut, WrinkleOut


@dataclass(frozen=True)
class TriageThresholds:
    acne_min_severity_prob: float = 0.5
    wrinkle_min_confidence: float = 0.5
    under_eye_uncertain_low: float = 0.4
    under_eye_uncertain_high: float = 0.6
    refer_severities: tuple[str, ...] = ("very_severe",)
    version: str = "0.1.0-provisional"


DEFAULT_THRESHOLDS = TriageThresholds()


def triage(
    quality: QualityOut,
    acne: AcneOut | None,
    wrinkles: WrinkleOut | None,
    under_eye: UnderEyeOut | None,
    t: TriageThresholds = DEFAULT_THRESHOLDS,
) -> TriageOut:
    if quality.status == "retake":
        return TriageOut(action="retake", reasons=quality.reasons)
    if quality.status == "out_of_scope":
        return TriageOut(action="retake", reasons=["image_out_of_scope", *quality.reasons])

    reasons: list[str] = []
    if acne and acne.severity in t.refer_severities:
        return TriageOut(action="refer_dermatologist", reasons=["severity_outside_cosmetic_scope"])
    if acne and max(acne.severity_probabilities) < t.acne_min_severity_prob:
        reasons.append("low_confidence_acne")
    if wrinkles and wrinkles.mean_confidence < t.wrinkle_min_confidence:
        reasons.append("low_confidence_wrinkles")
    if under_eye and t.under_eye_uncertain_low <= under_eye.probability <= t.under_eye_uncertain_high:
        reasons.append("uncertain_under_eye")
    return TriageOut(action="limited" if reasons else "proceed", reasons=reasons)
