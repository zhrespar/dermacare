from typing import Literal

from pydantic import BaseModel, Field

Need = Literal["acne_care", "wrinkle_care", "under_eye_care", "hydration", "sun_protection"]


class ProfileIn(BaseModel):
    skin_type: Literal["dry", "oily", "combination", "normal"] | None = None
    sensitivity: Literal["none", "mild", "high"] | None = None
    allergies: list[str] | None = Field(default=None, description="INCI names; null = not answered")
    avoid_ingredients: list[str] = []
    past_reaction_ingredients: list[str] = Field(
        default=[], description="INCI names linked to the user's past adverse reactions; hard-excluded"
    )
    goals: list[Need] = []
    budget_max: float | None = Field(default=None, ge=0)
    preferred_categories: list[str] = []


class FindingsIn(BaseModel):
    acne_severity: Literal["mild", "moderate", "severe", "very_severe"] | None = None
    wrinkle_area_ratio: float | None = Field(default=None, ge=0, le=1)
    under_eye_present: bool | None = None
    triage_action: Literal["proceed", "limited", "refer_dermatologist", "retake"] | None = Field(
        default=None, description="From the analysis; findings are used only when 'proceed'"
    )
    is_mock: bool = False


class ProductIn(BaseModel):
    id: str
    brand: str
    manufacturer: str | None = None
    name: str
    category: str
    routine_slot: Literal["am", "pm", "both"]
    inci: list[str]
    key_ingredients: list[str] = []
    targets: list[Need] = []
    warnings: list[str] = []
    suitable_skin_types: list[str] = []
    price: float | None = None
    currency: str | None = None
    available: bool | None = None
    usage_instructions: str | None = None
    source_url: str | None = None
    verification_status: Literal["pending", "verified", "rejected"]


class RecommendationRequest(BaseModel):
    mode: Literal["profile_only", "image_only", "multimodal"] = "multimodal"
    profile: ProfileIn | None = None
    findings: FindingsIn | None = None


class ScoreBreakdown(BaseModel):
    need_ingredient: float = Field(ge=0, le=50)
    profile_goal: float = Field(ge=0, le=25)
    routine_category: float = Field(ge=0, le=15)
    preference: float = Field(ge=0, le=10)


class RankedProduct(BaseModel):
    product_id: str
    brand: str
    name: str
    routine_slot: str
    total_score: float
    breakdown: ScoreBreakdown
    reasons: list[str]


class ExcludedProduct(BaseModel):
    product_id: str
    reasons: list[str]


class RoutineStep(BaseModel):
    step: int
    category: str
    product_id: str
    usage_instructions: str | None = None


class SkippedStep(BaseModel):
    product_id: str
    reason: str


class RecommendationResponse(BaseModel):
    rules_version: str
    mode: str
    needs: list[Need]
    missing_information: list[str]
    morning: list[RankedProduct]
    evening: list[RankedProduct]
    morning_routine: list[RoutineStep] = []
    evening_routine: list[RoutineStep] = []
    skipped_for_compatibility: list[SkippedStep] = []
    excluded: list[ExcludedProduct]
    pending_rules: list[str] = Field(
        default=[], description="Needs whose ingredient rule awaits expert review"
    )
