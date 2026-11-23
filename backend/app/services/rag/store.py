"""Vector stores: in-memory (dev/tests) and PostgreSQL + pgvector."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.services.rag.documents import Chunk, SourceDocument


@dataclass(frozen=True)
class ScoredChunk:
    chunk: Chunk
    score: float  # cosine similarity, higher is better


class VectorStore(Protocol):
    def add(self, chunks: list[Chunk], vectors: list[list[float]], embedding_model: str) -> None: ...
    def search(self, vector: list[float], k: int, topics: set[str] | None = None) -> list[ScoredChunk]: ...


class InMemoryVectorStore:
    def __init__(self) -> None:
        self._rows: list[tuple[Chunk, list[float]]] = []

    def __len__(self) -> int:
        return len(self._rows)

    def add(self, chunks, vectors, embedding_model):
        self._rows.extend(zip(chunks, vectors, strict=True))

    def search(self, vector, k, topics=None):
        rows = [(c, v) for c, v in self._rows if not topics or not c.doc.topics or topics & set(c.doc.topics)]
        scored = [ScoredChunk(c, sum(a * b for a, b in zip(vector, v, strict=True))) for c, v in rows]
        scored.sort(key=lambda s: (-s.score, s.chunk.chunk_id))
        return scored[:k]


class PgVectorStore:
    """Uses knowledge_documents / knowledge_chunks (see app.models.knowledge)."""

    def __init__(self, session_factory) -> None:
        self._sf = session_factory

    def add(self, chunks, vectors, embedding_model):
        from app.models.knowledge import KnowledgeChunk, KnowledgeDocument

        with self._sf() as db:
            for c, v in zip(chunks, vectors, strict=True):
                d = c.doc
                if db.get(KnowledgeDocument, d.doc_id) is None:
                    db.add(
                        KnowledgeDocument(
                            id=d.doc_id,
                            title=d.title,
                            source_type=d.source_type,
                            source_url=d.source_url,
                            publisher=d.publisher,
                            accessed_at=d.accessed_at,
                            license=d.license,
                            verification_status=d.verification_status,
                            language=d.language,
                            topics=list(d.topics),
                        )
                    )
                    db.flush()
                db.merge(
                    KnowledgeChunk(
                        id=c.chunk_id,
                        document_id=d.doc_id,
                        position=c.position,
                        text=c.text,
                        embedding=v,
                        embedding_model=embedding_model,
                    )
                )
            db.commit()

    def search(self, vector, k, topics=None):
        from sqlalchemy import select

        from app.models.knowledge import KnowledgeChunk, KnowledgeDocument

        dist = KnowledgeChunk.embedding.cosine_distance(vector)
        q = (
            select(KnowledgeChunk, KnowledgeDocument, dist.label("d"))
            .join(KnowledgeDocument)
            .where(KnowledgeDocument.verification_status == "verified")
            .order_by(dist)
            .limit(k)
        )
        out = []
        with self._sf() as db:
            for ch, doc, d in db.execute(q):
                if topics and doc.topics and not topics & set(doc.topics):
                    continue
                sd = SourceDocument(
                    doc.id,
                    doc.title,
                    doc.source_type,
                    doc.source_url,
                    doc.publisher,
                    doc.accessed_at,
                    doc.license,
                    doc.verification_status,
                    doc.language,
                    tuple(doc.topics or ()),
                )
                out.append(ScoredChunk(Chunk(ch.id, sd, ch.text, ch.position), 1.0 - float(d)))
        return out
