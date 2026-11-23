"""Auth, profile and account deletion."""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import delete, select

from app.api.deps import DB, CurrentUser
from app.core.security import create_access_token, hash_password, verify_password
from app.models import Analysis, FaceImage, Recommendation, RecommendationItem, SkinProfile, User
from app.schemas.account import LoginIn, ProfileData, RegisterIn, Token

router = APIRouter(tags=["account"])


@router.post("/auth/register", response_model=Token, status_code=201)
def register(body: RegisterIn, db: DB) -> Token:
    email = body.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "email_already_registered")
    user = User(
        email=email,
        password_hash=hash_password(body.password),
        is_active=True,
        consent_version=body.consent_version,
        consent_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.commit()
    return Token(access_token=create_access_token(user.id))


@router.post("/auth/login", response_model=Token)
def login(body: LoginIn, db: DB) -> Token:
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if user is None or user.deleted_at or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid_credentials")
    return Token(access_token=create_access_token(user.id))


def latest_profile(db, user: User) -> SkinProfile | None:
    return db.scalar(
        select(SkinProfile)
        .where(SkinProfile.user_id == user.id)
        .order_by(SkinProfile.created_at.desc(), SkinProfile.id)
        .limit(1)
    )


def profile_to_data(p: SkinProfile | None) -> ProfileData:
    if p is None:
        return ProfileData()
    prefs = p.preferences or {}
    return ProfileData(
        skin_type=p.skin_type,
        sensitivity=p.sensitivity,
        allergies=p.allergies,
        avoid_ingredients=p.avoid_ingredients or [],
        past_reaction_ingredients=p.past_reaction_ingredients or [],
        past_reactions=p.past_reactions,
        goals=p.goals or [],
        budget_max=float(p.budget_max) if p.budget_max is not None else None,
        currency=p.currency,
        preferred_categories=prefs.get("preferred_categories", []),
    )


@router.get("/profile", response_model=ProfileData)
def get_profile(user: CurrentUser, db: DB) -> ProfileData:
    return profile_to_data(latest_profile(db, user))


@router.put("/profile", response_model=ProfileData)
def put_profile(body: ProfileData, user: CurrentUser, db: DB) -> ProfileData:
    p = latest_profile(db, user)
    if p is None:
        p = SkinProfile(user_id=user.id)
        db.add(p)
    p.skin_type = body.skin_type
    p.sensitivity = body.sensitivity
    p.allergies = body.allergies
    p.avoid_ingredients = body.avoid_ingredients
    p.past_reaction_ingredients = body.past_reaction_ingredients
    p.past_reactions = body.past_reactions
    p.goals = list(body.goals)
    p.budget_max = body.budget_max
    p.currency = body.currency
    p.preferences = {"preferred_categories": body.preferred_categories}
    db.commit()
    return body


@router.delete("/me", status_code=204)
def delete_me(user: CurrentUser, db: DB) -> Response:
    """Hard-delete the account and all personal data (profile, images metadata, analyses, recommendations)."""
    rec_ids = select(Recommendation.id).where(Recommendation.user_id == user.id)
    db.execute(delete(RecommendationItem).where(RecommendationItem.recommendation_id.in_(rec_ids)))
    for model in (Recommendation, Analysis, FaceImage, SkinProfile):
        db.execute(delete(model).where(model.user_id == user.id))
    db.delete(user)
    db.commit()
    # Object-storage images are deleted by key once storage exists (mock path stores none).
    return Response(status_code=204)
