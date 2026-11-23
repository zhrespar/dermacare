from typing import Literal

from pydantic import BaseModel, Field


class BoxOut(BaseModel):
    x_min: float = Field(ge=0, le=1)
    y_min: float = Field(ge=0, le=1)
    x_max: float = Field(ge=0, le=1)
    y_max: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    region: str | None = Field(default=None, description="Facial region the box centre falls in")


class AcneOut(BaseModel):
    lesion_count: int
    lesions: list[BoxOut]
    severity: Literal["mild", "moderate", "severe", "very_severe"]
    severity_probabilities: list[float] = Field(min_length=4, max_length=4)


class WrinkleOut(BaseModel):
    affected_area_ratio: float = Field(ge=0, le=1)
    mean_confidence: float = Field(ge=0, le=1)
    mask_url: str | None = None


class UnderEyeOut(BaseModel):
    present: bool
    probability: float = Field(ge=0, le=1)
    gradcam_url: str | None = None


class QualityOut(BaseModel):
    status: Literal["accepted", "retake", "out_of_scope"]
    reasons: list[str]


class TriageOut(BaseModel):
    action: Literal["proceed", "limited", "refer_dermatologist", "retake"]
    reasons: list[str]


class RegionSummary(BaseModel):
    region: str
    lesion_count: int


class AnalysisResponse(BaseModel):
    id: str
    is_mock: bool = Field(description="True when produced by placeholder models. Never real results.")
    quality: QualityOut
    triage: TriageOut
    acne: AcneOut | None
    wrinkles: WrinkleOut | None
    under_eye: UnderEyeOut | None
    regions: list[RegionSummary] = []
    model_versions: dict[str, str]
    thresholds_version: str | None = None
    disclaimer: str
