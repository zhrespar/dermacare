"""HTTP adapters for Anthropic, OpenAI and Google Gemini (no vendor SDKs required).

Nothing here assumes a paid plan or a default model: a provider is only built when
LLM_PROVIDER, LLM_MODEL and that provider's API key are all set. Keys are read from
settings (environment), never hardcoded, never logged.
"""

from __future__ import annotations

import time

import httpx

from app.core.config import Settings
from app.services.llm.base import LLMProvider, LLMRequest, LLMResponse, LLMUnavailable, estimate_cost


class DisabledProvider:
    name = "disabled"
    model = "none"

    def generate(self, req: LLMRequest) -> LLMResponse:
        raise LLMUnavailable("LLM provider is disabled")


class _HTTPProvider:
    name = "base"
    url = ""

    def __init__(
        self,
        api_key: str,
        model: str,
        timeout_s: float = 30.0,
        price_in: float | None = None,
        price_out: float | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self._key = api_key
        self.model = model
        self._price_in, self._price_out = price_in, price_out
        self._client = client or httpx.Client(timeout=timeout_s)

    # subclass hooks
    def _request(self, req: LLMRequest) -> tuple[str, dict, dict]: ...
    def _parse(self, data: dict) -> tuple[str, int | None, int | None, str | None]: ...

    def generate(self, req: LLMRequest) -> LLMResponse:
        url, headers, body = self._request(req)
        t0 = time.perf_counter()
        try:
            r = self._client.post(url, headers=headers, json=body)
            r.raise_for_status()
            text, tin, tout, finish = self._parse(r.json())
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as e:
            raise LLMUnavailable(f"{self.name} call failed: {type(e).__name__}") from None
        ms = (time.perf_counter() - t0) * 1000
        return LLMResponse(
            text=text,
            provider=self.name,
            model=self.model,
            latency_ms=round(ms, 1),
            input_tokens=tin,
            output_tokens=tout,
            est_cost_usd=estimate_cost(tin, tout, self._price_in, self._price_out),
            raw_finish_reason=finish,
        )


class AnthropicProvider(_HTTPProvider):
    name = "anthropic"
    url = "https://api.anthropic.com/v1/messages"

    def _request(self, req):
        headers = {
            "x-api-key": self._key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        body = {
            "model": self.model,
            "max_tokens": req.max_output_tokens,
            "temperature": req.temperature,
            "system": req.system,
            "messages": [{"role": "user", "content": req.user}],
        }
        return self.url, headers, body

    def _parse(self, d):
        text = "".join(b.get("text", "") for b in d["content"] if b.get("type") == "text")
        u = d.get("usage", {})
        return text, u.get("input_tokens"), u.get("output_tokens"), d.get("stop_reason")


class OpenAIProvider(_HTTPProvider):
    name = "openai"
    url = "https://api.openai.com/v1/chat/completions"

    def _request(self, req):
        headers = {"Authorization": f"Bearer {self._key}", "content-type": "application/json"}
        body = {
            "model": self.model,
            "max_completion_tokens": req.max_output_tokens,
            "temperature": req.temperature,
            "messages": [{"role": "system", "content": req.system}, {"role": "user", "content": req.user}],
        }
        return self.url, headers, body

    def _parse(self, d):
        c = d["choices"][0]
        u = d.get("usage", {})
        return (
            c["message"]["content"] or "",
            u.get("prompt_tokens"),
            u.get("completion_tokens"),
            c.get("finish_reason"),
        )


class GeminiProvider(_HTTPProvider):
    name = "gemini"
    url = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    def _request(self, req):
        headers = {"x-goog-api-key": self._key, "content-type": "application/json"}
        body = {
            "systemInstruction": {"parts": [{"text": req.system}]},
            "contents": [{"role": "user", "parts": [{"text": req.user}]}],
            "generationConfig": {"maxOutputTokens": req.max_output_tokens, "temperature": req.temperature},
        }
        return self.url.format(model=self.model), headers, body

    def _parse(self, d):
        cand = d["candidates"][0]
        text = "".join(p.get("text", "") for p in cand["content"]["parts"])
        u = d.get("usageMetadata", {})
        return text, u.get("promptTokenCount"), u.get("candidatesTokenCount"), cand.get("finishReason")


_REGISTRY = {"anthropic": AnthropicProvider, "openai": OpenAIProvider, "gemini": GeminiProvider}


def build_provider(s: Settings, name: str | None = None, client: httpx.Client | None = None) -> LLMProvider:
    name = name or s.llm_provider
    if name == "disabled":
        return DisabledProvider()
    key = getattr(s, f"{name}_api_key", None)
    if key is None or not key.get_secret_value() or not s.llm_model:
        # Not configured -> behave as disabled; never guess keys or models.
        return DisabledProvider()
    return _REGISTRY[name](
        key.get_secret_value(),
        s.llm_model,
        s.llm_timeout_s,
        s.llm_price_input_per_mtok,
        s.llm_price_output_per_mtok,
        client,
    )
