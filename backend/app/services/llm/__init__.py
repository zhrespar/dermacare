"""Ready-made LLMs behind one interface, used ONLY to explain validated recommendations."""

from app.services.llm.base import LLMProvider, LLMRequest, LLMResponse, LLMUnavailable, estimate_cost
from app.services.llm.compare import ComparisonRow, compare_providers
from app.services.llm.explain import explain, rule_template
from app.services.llm.guard import GuardReport, check_output
from app.services.llm.providers import (
    AnthropicProvider,
    DisabledProvider,
    GeminiProvider,
    OpenAIProvider,
    build_provider,
)

__all__ = [
    "AnthropicProvider",
    "ComparisonRow",
    "DisabledProvider",
    "GeminiProvider",
    "GuardReport",
    "LLMProvider",
    "LLMRequest",
    "LLMResponse",
    "LLMUnavailable",
    "OpenAIProvider",
    "build_provider",
    "check_output",
    "compare_providers",
    "estimate_cost",
    "explain",
    "rule_template",
]
