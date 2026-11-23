"""RAG/LLM explanation provider interface.

The LLM only rephrases already-computed, rule-based reasons using retrieved, verified
documents. It never selects products, never diagnoses. Default provider is `disabled`
so no paid API calls happen unless explicitly configured.
"""

from __future__ import annotations

from typing import Protocol


class ExplanationProvider(Protocol):
    def explain(self, reasons: list[str], context_docs: list[str]) -> str: ...


class DisabledProvider:
    def explain(self, reasons: list[str], context_docs: list[str]) -> str:
        return "; ".join(reasons)


def get_provider(name: str) -> ExplanationProvider:
    if name == "disabled":
        return DisabledProvider()
    raise NotImplementedError(f"LLM provider '{name}' is not implemented yet")
