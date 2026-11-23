"""Provider-independent LLM contract.

Business logic depends only on `LLMProvider.generate(LLMRequest) -> LLMResponse`, so providers
(Anthropic, OpenAI, Gemini) can be swapped and compared without touching it. Every response
carries latency, token usage and a cost estimate (None when prices are not configured).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


class LLMUnavailable(RuntimeError):
    """Provider disabled, not configured, or the call failed. Callers fall back to rule text."""


@dataclass(frozen=True)
class LLMRequest:
    system: str
    user: str
    max_output_tokens: int = 600
    temperature: float = 0.2
    purpose: str = "explanation"


@dataclass(frozen=True)
class LLMResponse:
    text: str
    provider: str
    model: str
    latency_ms: float
    input_tokens: int | None = None
    output_tokens: int | None = None
    est_cost_usd: float | None = None
    raw_finish_reason: str | None = None
    extra: dict = field(default_factory=dict)


class LLMProvider(Protocol):
    name: str
    model: str

    def generate(self, req: LLMRequest) -> LLMResponse: ...


def estimate_cost(
    input_tokens: int | None,
    output_tokens: int | None,
    price_in_per_mtok: float | None,
    price_out_per_mtok: float | None,
) -> float | None:
    if None in (input_tokens, output_tokens, price_in_per_mtok, price_out_per_mtok):
        return None
    return round(input_tokens * price_in_per_mtok / 1e6 + output_tokens * price_out_per_mtok / 1e6, 6)
