import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.deps import DB, CurrentUser
from app.api.routes.account import latest_profile, profile_to_data
from app.models import Analysis, Recommendation, RecommendationItem
from app.schemas.recommendation import FindingsIn, ProfileIn, RecommendationRequest, RecommendationResponse
from app.services.catalog import current_version, load_catalog
from app.services.recommendation import recommend

router = APIRouter(prefix="/recommendations", tags=["recommendation"])


@router.post("/preview", response_model=RecommendationResponse)
def preview(req: RecommendationRequest) -> RecommendationResponse:
    """Stateless engine run on explicit input against an empty catalog (contract testing)."""
    return recommend(req, catalog=[])


class StoredRecommendationRequest(BaseModel):
    analysis_id: uuid.UUID | None = None
    mode: str | None = None  # default: multimodal with analysis, profile_only without


class StoredRecommendationResponse(RecommendationResponse):
    recommendation_id: str | None = None
    catalog_version: str | None = None


def findings_from(a: Analysis) -> FindingsIn:
    return FindingsIn(
        acne_severity=(a.acne or {}).get("severity"),
        wrinkle_area_ratio=(a.wrinkles or {}).get("affected_area_ratio"),
        under_eye_present=(a.under_eye or {}).get("present"),
        triage_action=(a.triage or {}).get("action"),
        is_mock=a.is_mock,
    )


@router.post("", response_model=StoredRecommendationResponse)
def create(body: StoredRecommendationRequest, user: CurrentUser, db: DB) -> StoredRecommendationResponse:
    """Stored profile + (optional) stored analysis + current catalog version -> persisted recommendation."""
    analysis = None
    if body.analysis_id:
        analysis = db.get(Analysis, body.analysis_id)
        if analysis is None or analysis.user_id != user.id:
            raise HTTPException(404, "analysis_not_found")
    mode = body.mode or ("multimodal" if analysis else "profile_only")
    if mode not in ("profile_only", "image_only", "multimodal"):
        raise HTTPException(422, "bad_mode")
    pd = profile_to_data(latest_profile(db, user))
    req = RecommendationRequest(
        mode=mode,
        profile=ProfileIn(**pd.model_dump(exclude={"past_reactions", "currency"})),
        findings=findings_from(analysis) if analysis else None,
    )
    version = current_version(db)
    res = recommend(req, load_catalog(db, version.id) if version else [])
    out = StoredRecommendationResponse(**res.model_dump(), catalog_version=version.label if version else None)
    if version is None:
        out.missing_information.append("no_catalog_version")
        return out
    rec = Recommendation(
        user_id=user.id,
        analysis_id=analysis.id if analysis else None,
        catalog_version_id=version.id,
        rules_version=res.rules_version,
        mode=mode,
        needs=list(res.needs),
    )
    for slot, steps in (("am", res.morning_routine), ("pm", res.evening_routine)):
        scores = {r.product_id: r for r in (res.morning if slot == "am" else res.evening)}
        for s in steps:
            r = scores[s.product_id]
            rec.items.append(
                RecommendationItem(
                    product_id=uuid.UUID(s.product_id),
                    routine_slot=slot,
                    step_order=s.step,
                    total_score=r.total_score,
                    score_breakdown=r.breakdown.model_dump(),
                    reasons=r.reasons,
                )
            )
    db.add(rec)
    db.commit()
    out.recommendation_id = str(rec.id)
    return out
