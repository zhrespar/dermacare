"""Embedding backends (configurable).

- SentenceTransformerEmbedder: pretrained model (RAG_EMBEDDING_MODEL), loaded lazily; needs
  `pip install sentence-transformers` (not in the base backend image).
- HashingEmbedder: deterministic lexical hashing. NOT semantic — for tests and offline dev only.
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol

_TOKEN = re.compile(r"[\wçğıöşü]+", re.I)


class Embedder(Protocol):
    model_id: str
    dim: int

    def embed(self, texts: list[str]) -> list[list[float]]: ...


def _l2(v: list[float]) -> list[float]:
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


class HashingEmbedder:
    def __init__(self, dim: int = 384) -> None:
        self.dim = dim
        self.model_id = f"hashing-{dim}-dev-only"

    def embed(self, texts: list[str]) -> list[list[float]]:
        out = []
        for t in texts:
            v = [0.0] * self.dim
            for tok in _TOKEN.findall(t.lower()):
                h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
                v[h % self.dim] += 1.0 if (h >> 64) & 1 else -1.0
            out.append(_l2(v))
        return out


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str, dim: int) -> None:
        self.model_id = model_name
        self.dim = dim
        self._model = None

    def embed(self, texts: list[str]) -> list[list[float]]:
        if self._model is None:
            from sentence_transformers import SentenceTransformer  # lazy, optional dependency

            self._model = SentenceTransformer(self.model_id)
        vecs = self._model.encode(texts, normalize_embeddings=True)
        if len(vecs[0]) != self.dim:
            raise ValueError(f"model dim {len(vecs[0])} != RAG_EMBEDDING_DIM {self.dim}")
        return [list(map(float, v)) for v in vecs]


def build_embedder(backend: str, model_name: str, dim: int) -> Embedder:
    if backend == "sentence_transformers":
        return SentenceTransformerEmbedder(model_name, dim)
    return HashingEmbedder(dim)
