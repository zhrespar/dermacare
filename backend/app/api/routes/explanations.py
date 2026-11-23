import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import DB, get_llm_provider, get_retriever
from app.core.config import get_settings
from app.models import LLMCallLog
from app.schemas.explanation import ExplanationRequest, ExplanationResponse
from app.services.llm import LLMProvider, explain
from app.services.rag import Retriever

router = APIRouter(prefix="/explanations", tags=["explanation"])
log = logging.getLogger(__name__)


def record_call(db, e: ExplanationResponse, purpose: str = "explanation") -> None:
    """Store metrics only (no prompt text, no user id). Never fails the request."""
    m = e.metrics
    try:
        db.add(
            LLMCallLog(
                purpose=purpose,
                provider=e.provider,
                model=e.model,
                mode=e.mode,
                fallback_reason=e.fallback_reason,
                latency_ms=m.latency_ms,
                input_tokens=m.input_tokens,
                output_tokens=m.output_tokens,
                est_cost_usd=m.est_cost_usd,
                grounded_ratio=m.grounded_ratio,
                safe=m.safe,
                rules_version=e.rules_version,
            )
        )
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        log.warning("llm_call_log_not_saved")


@router.post("", response_model=ExplanationResponse)
def create_explanation(
    req: ExplanationRequest,
    db: DB,
    retriever: Annotated[Retriever, Depends(get_retriever)],
    provider: Annotated[LLMProvider, Depends(get_llm_provider)],
) -> ExplanationResponse:
    """Explain an engine result. Falls back to rule text when no verified sources / LLM disabled."""
    s = get_settings()
    e = explain(
        req.recommendation, retriever, provider, req.language, s.llm_max_output_tokens, s.llm_temperature
    )
    if e.provider != "none":  # only real LLM attempts are worth logging
        record_call(db, e)
    return e
