"""LLM providers (mocked HTTP), guard, RAG and explanation flow.

All knowledge documents here are SYNTHETIC FIXTURES (example.invalid URLs), not real sources.
No network calls are made.
"""

from datetime import date

import httpx
import pytest
from app.core.config import Settings
from app.schemas.recommendation import FindingsIn, ProductIn, ProfileIn, RecommendationRequest
from app.services.llm import (
    AnthropicProvider,
    DisabledProvider,
    GeminiProvider,
    LLMRequest,
    LLMResponse,
    OpenAIProvider,
    build_provider,
    check_output,
    estimate_cost,
    explain,
)
from app.services.rag import (
    HashingEmbedder,
    InMemoryVectorStore,
    Retriever,
    SourceDocument,
    UnverifiedSourceError,
    chunk_text,
)
from app.services.recommendation import recommend


def _doc(i="FIX1", status="verified", topics=("acne_care",)):
    return SourceDocument(
        doc_id=i,
        title=f"Fixture source {i}",
        source_type="scientific",
        source_url=f"https://example.invalid/{i}",
        publisher="FIXTURE",
        accessed_at=date(2026, 1, 1),
        license="fixture",
        verification_status=status,
        topics=topics,
    )


FIXTURE_TEXT = (
    "Cosmetic care for acne-prone skin ingredients are described in this fixture paragraph. "
    "Gentle cleansing is part of a cosmetic routine for acne-prone skin.\n\n"
    "Daily sunscreen use and sun protection is discussed in a second fixture paragraph."
)


def _retriever(min_score=0.05):
    r = Retriever(HashingEmbedder(384), InMemoryVectorStore(), top_k=3, min_score=min_score)
    r.ingest(_doc(), FIXTURE_TEXT, max_chars=120)
    return r


def _rec():
    p = ProductIn(
        id="FIXTURE-A",
        brand="FIXTURE",
        name="Serum",
        category="serum",
        routine_slot="pm",
        inci=["AQUA"],
        targets=["acne_care"],
        verification_status="verified",
    )
    req = RecommendationRequest(
        profile=ProfileIn(skin_type="oily", sensitivity="none", allergies=[]),
        findings=FindingsIn(acne_severity="mild", triage_action="proceed"),
    )
    return recommend(req, [p])


class FakeProvider:
    name, model = "fake", "fake-1"

    def __init__(self, text):
        self.text = text

    def generate(self, req: LLMRequest) -> LLMResponse:
        assert "VALIDATED_RECOMMENDATIONS" in req.user and "[S1]" in req.user
        return LLMResponse(self.text, self.name, self.model, 12.0, 100, 20, None)


# ---- providers -------------------------------------------------------------


def _client(payload, seen):
    def handler(request: httpx.Request):
        seen.append(request)
        return httpx.Response(200, json=payload)

    return httpx.Client(transport=httpx.MockTransport(handler))


@pytest.mark.parametrize(
    "cls,payload,key_header",
    [
        (
            AnthropicProvider,
            {
                "content": [{"type": "text", "text": "hi"}],
                "usage": {"input_tokens": 10, "output_tokens": 2},
                "stop_reason": "end_turn",
            },
            "x-api-key",
        ),
        (
            OpenAIProvider,
            {
                "choices": [{"message": {"content": "hi"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 2},
            },
            "authorization",
        ),
        (
            GeminiProvider,
            {
                "candidates": [{"content": {"parts": [{"text": "hi"}]}, "finishReason": "STOP"}],
                "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 2},
            },
            "x-goog-api-key",
        ),
    ],
)
def test_provider_adapters_parse_and_measure(cls, payload, key_header):
    seen = []
    p = cls("test-key", "test-model", price_in=1.0, price_out=2.0, client=_client(payload, seen))
    r = p.generate(LLMRequest("sys", "user"))
    assert (r.text, r.input_tokens, r.output_tokens) == ("hi", 10, 2)
    assert r.est_cost_usd == pytest.approx(10 / 1e6 + 4 / 1e6)
    assert r.latency_ms >= 0 and key_header in seen[0].headers


def test_build_provider_requires_key_and_model():
    assert isinstance(build_provider(Settings(llm_provider="anthropic")), DisabledProvider)
    assert isinstance(build_provider(Settings(llm_provider="openai", openai_api_key="k")), DisabledProvider)
    p = build_provider(Settings(llm_provider="gemini", gemini_api_key="k", llm_model="m"))
    assert isinstance(p, GeminiProvider) and p.model == "m"


def test_cost_unknown_without_prices():
    assert estimate_cost(10, 10, None, None) is None


# ---- guard -----------------------------------------------------------------


def test_guard_flags_hallucinated_citations_unknown_products_and_medical_terms():
    r = check_output("Use {P:X}. [S9] This will cure acne [S1].", {"S1"}, {"Y"}, {"X"})
    assert r.invalid_citations == ["S9"] and r.unknown_products == ["X"]
    assert "cure" in r.flagged_terms and not r.passes()


# ---- RAG -------------------------------------------------------------------


def test_chunking_respects_size_and_metadata():
    chunks = chunk_text(_doc(), FIXTURE_TEXT, max_chars=120)
    assert len(chunks) >= 2 and all(c.doc.doc_id == "FIX1" for c in chunks)
    assert chunks[0].chunk_id == "FIX1#0"


def test_unverified_sources_are_rejected():
    r = Retriever(HashingEmbedder(), InMemoryVectorStore())
    with pytest.raises(UnverifiedSourceError):
        r.ingest(_doc(status="pending"), FIXTURE_TEXT)


def test_retrieval_filters_by_topic_and_score():
    r = _retriever()
    assert r.retrieve("cosmetic care for acne-prone skin", topics={"acne_care"})
    assert r.retrieve("cosmetic care for acne-prone skin", topics={"wrinkle_care"}) == []


# ---- explanation -------------------------------------------------------------


def test_no_sources_means_no_llm_and_no_citations():
    empty = Retriever(HashingEmbedder(), InMemoryVectorStore())
    e = explain(_rec(), empty, FakeProvider("should not be called"), "en")
    assert e.mode == "rule_template" and e.fallback_reason == "no_verified_sources" and e.citations == []
    assert "FIXTURE Serum" in e.text


def test_disabled_provider_falls_back():
    e = explain(_rec(), _retriever(), DisabledProvider(), "en")
    assert e.fallback_reason == "llm_disabled" and e.citations == []


def test_grounded_llm_answer_is_accepted_with_real_citations():
    e = explain(_rec(), _retriever(), FakeProvider("{P:FIXTURE-A} fits your routine [S1]."), "en")
    assert e.mode == "llm_grounded"
    assert e.text == "FIXTURE Serum fits your routine [S1]."
    assert [c.doc_id for c in e.citations] == ["FIX1"]
    assert e.metrics.grounded_ratio == 1.0 and e.metrics.safe


@pytest.mark.parametrize(
    "text",
    [
        "{P:FIXTURE-A} fits [S7].",  # invented citation
        "{P:OTHER} is better [S1].",  # product not validated by the engine
        "This diagnosis shows acne [S1].",  # medical wording
        "{P:FIXTURE-A} fits. No citation here. Nor here [S1].",  # weakly grounded
    ],
)
def test_guard_rejections_fall_back_to_rules(text):
    e = explain(_rec(), _retriever(), FakeProvider(text), "en")
    assert e.mode == "rule_template" and e.fallback_reason == "guard_rejected" and e.citations == []


def test_explanation_endpoint_defaults_to_rule_template(client):
    body = {"recommendation": _rec().model_dump(), "language": "tr"}
    r = client.post("/api/v1/explanations", json=body)
    assert r.status_code == 200
    j = r.json()
    assert j["mode"] == "rule_template" and j["citations"] == [] and "Akşam 1" in j["text"]


def test_components_endpoint_lists_kinds(client):
    j = client.get("/api/v1/system/components").json()
    kinds = {c["kind"] for c in j["components"]}
    assert kinds == {"trained_by_project", "pretrained", "rule_based", "external_api"}
    assert j["active"]["llm_provider"] == "disabled"
