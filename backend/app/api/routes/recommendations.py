from fastapi import APIRouter

from app.schemas.recommendation import RecommendationRequest, RecommendationResponse
from app.services.recommendation import recommend

router = APIRouter(prefix="/recommendations", tags=["recommendation"])


@router.post("/preview", response_model=RecommendationResponse)
def preview(req: RecommendationRequest) -> RecommendationResponse:
    # No verified catalog exists yet; returns needs + missing info with an empty product list.
    # TODO: load the frozen catalog version from the database.
    return recommend(req, catalog=[])
