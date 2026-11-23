from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.recommendation import RecommendationResponse


class ExplanationRequest(BaseModel):
    recommendation: RecommendationResponse = Field(description="Output of the rule engine, unchanged")
    language: Literal["tr", "en"] = "tr"


class CitationOut(BaseModel):
    source_id: str
    doc_id: str
    title: str
    publisher: str
    source_url: str
    accessed_at: str
    chunk_id: str
    score: float


class ExplanationMetrics(BaseModel):
    latency_ms: float | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    est_cost_usd: float | None = None
    grounded_ratio: float | None = None
    safe: bool | None = None
    retrieved_chunks: int = 0


class ExplanationResponse(BaseModel):
    mode: Literal["llm_grounded", "rule_template"]
    text: str
    citations: list[CitationOut]
    provider: str
    model: str
    rules_version: str
    fallback_reason: str | None = None
    metrics: ExplanationMetrics
    disclaimer: str
