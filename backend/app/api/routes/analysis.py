from fastapi import APIRouter, HTTPException, UploadFile

from app.core.config import get_settings
from app.schemas.analysis import AnalysisResponse
from app.services.mock_analysis import run_mock_analysis

router = APIRouter(prefix="/analyses", tags=["analysis"])


@router.post("", response_model=AnalysisResponse)
async def create_analysis(image: UploadFile) -> AnalysisResponse:
    s = get_settings()
    data = await image.read()
    if len(data) > s.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail="image_too_large")
    if s.analysis_backend != "mock":
        raise HTTPException(status_code=503, detail="model_backend_not_available")
    # Image bytes are not persisted by the mock path.
    return run_mock_analysis(data)
