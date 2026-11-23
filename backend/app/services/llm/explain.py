"""Explain ALREADY-VALIDATED recommendations with retrieved, cited evidence.

Order of authority: rule engine (hard filters + scores) > retrieved verified sources > LLM wording.
The LLM receives only products that passed the hard filters and may not add, remove or re-rank
them. Output is checked (guard.py); on any failure the rule-based template is returned instead.
"""

from __future__ import annotations

import json
import re

from app.schemas.explanation import CitationOut, ExplanationMetrics, ExplanationResponse
from app.schemas.recommendation import RankedProduct, RecommendationResponse
from app.services.analysis import DISCLAIMER
from app.services.llm.base import LLMProvider, LLMRequest, LLMUnavailable
from app.services.llm.guard import CITATION_RE, check_output
from app.services.rag import Retriever, ScoredChunk, to_citations

PRODUCT_RE = re.compile(r"\{P:([^}]+)\}")
NEED_QUERIES = {
    "acne_care": "cosmetic care for acne-prone skin ingredients",
    "wrinkle_care": "cosmetic ingredients for fine lines and wrinkles",
    "under_eye_care": "under-eye area cosmetic care ingredients",
    "hydration": "skin hydration moisturizer ingredients",
    "sun_protection": "daily sunscreen use and sun protection",
}

SYSTEM_PROMPT = """You explain a cosmetic skincare routine that a rule-based engine has ALREADY selected.
Rules:
- Explain only the products listed in VALIDATED_RECOMMENDATIONS. Never add, remove, rank or replace products.
- Refer to a product only as {{P:<product_id>}}.
- Every sentence must cite at least one SOURCES entry as [S<n>]. Use only the given sources.
  If the sources do not support a statement, do not make it.
- This is cosmetic decision support, not medicine: never diagnose, name diseases, mention drugs,
  or promise treatment or cure. Suggest a dermatologist if the user has medical concerns.
- Write in {language}. Be brief: at most {max_sentences} sentences."""


def _ranked_index(rec: RecommendationResponse) -> dict[str, RankedProduct]:
    return {r.product_id: r for r in rec.morning + rec.evening}


def rule_template(rec: RecommendationResponse, language: str) -> str:
    idx = _ranked_index(rec)
    tr = language == "tr"
    lines: list[str] = []
    for label, steps in (
        ("Sabah" if tr else "Morning", rec.morning_routine),
        ("Akşam" if tr else "Evening", rec.evening_routine),
    ):
        for s in steps:
            r = idx[s.product_id]
            why = "; ".join(r.reasons) or ("kural eşleşmesi" if tr else "rule match")
            lines.append(
                f"{label} {s.step} ({s.category}): {r.brand} {r.name} — {why} [{r.total_score}/100]."
            )
    if not lines:
        lines.append(
            "Doğrulanmış katalogda profilinize uygun ürün bulunamadı."
            if tr
            else "No product in the verified catalog matched your profile."
        )
    if rec.missing_information:
        miss = ", ".join(rec.missing_information)
        lines.append(f"Eksik bilgi: {miss}." if tr else f"Missing information: {miss}.")
    return "\n".join(lines)


def _retrieve(rec: RecommendationResponse, retriever: Retriever) -> list[ScoredChunk]:
    seen: dict[str, ScoredChunk] = {}
    for need in rec.needs:
        for h in retriever.retrieve(NEED_QUERIES.get(need, need), topics={need}):
            if h.chunk.chunk_id not in seen or seen[h.chunk.chunk_id].score < h.score:
                seen[h.chunk.chunk_id] = h
    return sorted(seen.values(), key=lambda h: (-h.score, h.chunk.chunk_id))[: retriever.top_k]


def _fallback(rec, language, reason, n_hits=0) -> ExplanationResponse:
    return ExplanationResponse(
        mode="rule_template",
        text=rule_template(rec, language),
        citations=[],
        provider="none",
        model="none",
        rules_version=rec.rules_version,
        fallback_reason=reason,
        metrics=ExplanationMetrics(retrieved_chunks=n_hits),
        disclaimer=DISCLAIMER,
    )


def explain(
    rec: RecommendationResponse,
    retriever: Retriever,
    provider: LLMProvider,
    language: str = "tr",
    max_output_tokens: int = 600,
    temperature: float = 0.2,
    min_grounded: float = 0.6,
) -> ExplanationResponse:
    idx = _ranked_index(rec)
    if not idx:
        return _fallback(rec, language, "no_validated_products")
    hits = _retrieve(rec, retriever)
    if not hits:
        return _fallback(rec, language, "no_verified_sources")  # nothing to ground an LLM answer on
    if provider.name == "disabled":
        return _fallback(rec, language, "llm_disabled", len(hits))

    cites = to_citations(hits)
    sources = "\n".join(
        f"[{c.source_id}] {c.title} ({c.publisher}): {h.chunk.text}" for c, h in zip(cites, hits, strict=True)
    )
    items = [
        {
            "product_id": r.product_id,
            "brand": r.brand,
            "name": r.name,
            "slot": r.routine_slot,
            "score": r.total_score,
            "reasons": r.reasons,
        }
        for r in idx.values()
    ]
    user = (
        f"NEEDS: {json.dumps(rec.needs)}\n"
        f"VALIDATED_RECOMMENDATIONS: {json.dumps(items, ensure_ascii=False)}\n"
        f"MISSING_INFORMATION: {json.dumps(rec.missing_information)}\n"
        f"SOURCES:\n{sources}"
    )
    system = SYSTEM_PROMPT.format(language="Turkish" if language == "tr" else "English", max_sentences=8)
    try:
        resp = provider.generate(LLMRequest(system, user, max_output_tokens, temperature))
    except LLMUnavailable:
        return _fallback(rec, language, "llm_unavailable", len(hits))

    report = check_output(
        resp.text,
        {c.source_id for c in cites},
        set(idx),
        set(PRODUCT_RE.findall(resp.text)),
    )
    metrics = ExplanationMetrics(
        latency_ms=resp.latency_ms,
        input_tokens=resp.input_tokens,
        output_tokens=resp.output_tokens,
        est_cost_usd=resp.est_cost_usd,
        grounded_ratio=report.grounded_ratio,
        safe=report.safe,
        retrieved_chunks=len(hits),
    )
    if not report.passes(min_grounded):
        fb = _fallback(rec, language, "guard_rejected", len(hits))
        fb.metrics = metrics
        fb.provider, fb.model = resp.provider, resp.model
        return fb

    used = set(CITATION_RE.findall(resp.text))
    text = PRODUCT_RE.sub(lambda m: f"{idx[m.group(1)].brand} {idx[m.group(1)].name}", resp.text)
    return ExplanationResponse(
        mode="llm_grounded",
        text=text,
        citations=[CitationOut(**c.__dict__) for c in cites if c.source_id in used],
        provider=resp.provider,
        model=resp.model,
        rules_version=rec.rules_version,
        metrics=metrics,
        disclaimer=DISCLAIMER,
    )
