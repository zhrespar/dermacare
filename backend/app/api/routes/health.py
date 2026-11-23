from fastapi import APIRouter

from app import __version__
from app.core.config import get_settings
from app.db.session import check_database
from app.schemas.common import HealthResponse

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    s = get_settings()
    return HealthResponse(
        status="ok",
        version=__version__,
        environment=s.environment,
        database="ok" if check_database() else "unavailable",
        analysis_backend=s.analysis_backend,
    )
