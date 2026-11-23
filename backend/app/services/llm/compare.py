"""Run the same explanation scenario through several providers and collect comparable metrics.

Used for the later provider comparison (latency, cost estimate, groundedness, safety). It makes
real API calls only for providers that are configured; it never fabricates rows for others.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from app.schemas.recommendation import RecommendationResponse
from app.services.llm.base import LLMProvider
from app.services.llm.explain import explain
from app.services.rag import Retriever


@dataclass(frozen=True)
class ComparisonRow:
    scenario_id: str
    provider: str
    model: str
    mode: str
    fallback_reason: str | None
    latency_ms: float | None
    input_tokens: int | None
    output_tokens: int | None
    est_cost_usd: float | None
    grounded_ratio: float | None
    safe: bool | None
    n_citations: int

    def as_dict(self) -> dict:
        return asdict(self)


def compare_providers(
    scenarios: dict[str, RecommendationResponse],
    providers: list[LLMProvider],
    retriever: Retriever,
    language: str = "tr",
) -> list[ComparisonRow]:
    rows = []
    for sid, rec in scenarios.items():
        for p in providers:
            e = explain(rec, retriever, p, language)
            m = e.metrics
            rows.append(
                ComparisonRow(
                    sid,
                    p.name,
                    p.model,
                    e.mode,
                    e.fallback_reason,
                    m.latency_ms,
                    m.input_tokens,
                    m.output_tokens,
                    m.est_cost_usd,
                    m.grounded_ratio,
                    m.safe,
                    len(e.citations),
                )
            )
    return rows
