import uuid

from fastapi import APIRouter, HTTPException, UploadFile
from sqlalchemy import select

from app.api.deps import DB, CurrentUser, OptionalUser
from app.core.config import get_settings
from app.models import Analysis
from app.schemas.account import AnalysisSummary
from app.schemas.analysis import AnalysisResponse
from app.services.analysis import AnalysisBackendUnavailable, run_analysis

router = APIRouter(prefix="/analyses", tags=["analysis"])

_STATUS = {
    "proceed": "completed",
    "limited": "limited",
    "refer_dermatologist": "referred",
    "retake": "failed",
}


@router.post("", response_model=AnalysisResponse)
async def create_analysis(image: UploadFile, db: DB, user: OptionalUser) -> AnalysisResponse:
    """Anonymous calls are not stored. With a bearer token the result (never the image) is saved."""
    s = get_settings()
    data = await image.read()
    if len(data) > s.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail="image_too_large")
    try:
        res = run_analysis(data, s.analysis_backend)
    except AnalysisBackendUnavailable:
        raise HTTPException(status_code=503, detail="model_backend_not_available") from None
    if user is not None:
        row = Analysis(
            id=uuid.uuid4(),
            user_id=user.id,
            status=_STATUS[res.triage.action],
            is_mock=res.is_mock,
            acne=res.acne.model_dump() if res.acne else None,
            wrinkles=res.wrinkles.model_dump() if res.wrinkles else None,
            under_eye=res.under_eye.model_dump() if res.under_eye else None,
            triage=res.triage.model_dump(),
            model_versions=res.model_versions,
        )
        db.add(row)
        db.commit()
        res.id = str(row.id)
    return res


@router.get("", response_model=list[AnalysisSummary])
def history(user: CurrentUser, db: DB) -> list[AnalysisSummary]:
    rows = db.scalars(
        select(Analysis).where(Analysis.user_id == user.id).order_by(Analysis.created_at.desc()).limit(100)
    )
    return [
        AnalysisSummary(
            id=str(a.id),
            created_at=a.created_at,
            status=a.status,
            is_mock=a.is_mock,
            triage_action=(a.triage or {}).get("action"),
            model_versions=a.model_versions or {},
        )
        for a in rows
    ]
