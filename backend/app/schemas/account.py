from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

from app.schemas.recommendation import Need


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    consent_version: str = Field(min_length=1, max_length=32, description="Accepted privacy-notice version")


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ProfileData(BaseModel):
    """User-declared profile. null = not answered (never interpreted as 'no')."""

    skin_type: Literal["dry", "oily", "combination", "normal"] | None = None
    sensitivity: Literal["none", "mild", "high"] | None = None
    allergies: list[str] | None = None
    avoid_ingredients: list[str] = []
    past_reaction_ingredients: list[str] = []
    past_reactions: str | None = Field(default=None, max_length=2000)
    goals: list[Need] = []
    budget_max: float | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    preferred_categories: list[str] = []


class AnalysisSummary(BaseModel):
    id: str
    created_at: datetime
    status: str
    is_mock: bool
    triage_action: str | None
    model_versions: dict[str, str]
