from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_llm_provider, get_retriever
from app.core.config import get_settings
from app.schemas.explanation import ExplanationRequest, ExplanationResponse
from app.services.llm import LLMProvider, explain
from app.services.rag import Retriever

router = APIRouter(prefix="/explanations", tags=["explanation"])


@router.post("", response_model=ExplanationResponse)
def create_explanation(
    req: ExplanationRequest,
    retriever: Annotated[Retriever, Depends(get_retriever)],
    provider: Annotated[LLMProvider, Depends(get_llm_provider)],
) -> ExplanationResponse:
    """Explain an engine result. Falls back to rule text when no verified sources / LLM disabled."""
    s = get_settings()
    return explain(
        req.recommendation, retriever, provider, req.language, s.llm_max_output_tokens, s.llm_temperature
    )
