"""Retrieval-Augmented Generation over a VERIFIED skincare knowledge base.

RAG retrieves explanatory evidence for already-validated recommendations. It never selects
or filters products — exact product filtering stays in SQL + the rule engine.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.services.rag.documents import Chunk, SourceDocument, chunk_text
from app.services.rag.embeddings import Embedder, HashingEmbedder, build_embedder
from app.services.rag.store import InMemoryVectorStore, PgVectorStore, ScoredChunk, VectorStore


class UnverifiedSourceError(ValueError):
    pass


@dataclass(frozen=True)
class Citation:
    source_id: str  # "S1", "S2", ... as used in generated text
    doc_id: str
    title: str
    publisher: str
    source_url: str
    accessed_at: str
    chunk_id: str
    score: float


class Retriever:
    def __init__(self, embedder: Embedder, store: VectorStore, top_k: int = 5, min_score: float = 0.2):
        self.embedder, self.store, self.top_k, self.min_score = embedder, store, top_k, min_score

    def ingest(self, doc: SourceDocument, text: str, max_chars: int = 800) -> int:
        if doc.verification_status != "verified":
            raise UnverifiedSourceError(f"{doc.doc_id} is {doc.verification_status}; only verified sources")
        chunks = chunk_text(doc, text, max_chars=max_chars)
        self.store.add(chunks, self.embedder.embed([c.text for c in chunks]), self.embedder.model_id)
        return len(chunks)

    def retrieve(self, query: str, topics: set[str] | None = None) -> list[ScoredChunk]:
        vec = self.embedder.embed([query])[0]
        hits = self.store.search(vec, self.top_k, topics)
        return [
            h for h in hits if h.score >= self.min_score and h.chunk.doc.verification_status == "verified"
        ]


def to_citations(hits: list[ScoredChunk]) -> list[Citation]:
    return [
        Citation(
            source_id=f"S{i + 1}",
            doc_id=h.chunk.doc.doc_id,
            title=h.chunk.doc.title,
            publisher=h.chunk.doc.publisher,
            source_url=h.chunk.doc.source_url,
            accessed_at=h.chunk.doc.accessed_at.isoformat(),
            chunk_id=h.chunk.chunk_id,
            score=round(h.score, 4),
        )
        for i, h in enumerate(hits)
    ]


__all__ = [
    "Chunk",
    "Citation",
    "Embedder",
    "HashingEmbedder",
    "InMemoryVectorStore",
    "PgVectorStore",
    "Retriever",
    "ScoredChunk",
    "SourceDocument",
    "UnverifiedSourceError",
    "VectorStore",
    "build_embedder",
    "chunk_text",
    "to_citations",
]
