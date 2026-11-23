"""RAG knowledge base (pgvector) and LLM call metrics. Keep in sync with DATABASE_SCHEMA.md."""

from datetime import date, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

EMBEDDING_DIM = 384  # must equal RAG_EMBEDDING_DIM; changing it needs a migration + re-embedding


class KnowledgeDocument(Base):
    """Vetted source (scientific, guideline, ingredient DB, manufacturer). Only 'verified' is retrieved."""

    __tablename__ = "knowledge_documents"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(512))
    source_type: Mapped[str] = mapped_column(String(32))
    source_url: Mapped[str] = mapped_column(String(1024))
    publisher: Mapped[str] = mapped_column(String(255))
    accessed_at: Mapped[date] = mapped_column(Date)
    license: Mapped[str] = mapped_column(String(128))
    verification_status: Mapped[str] = mapped_column(String(16), index=True)
    language: Mapped[str] = mapped_column(String(8), default="en")
    topics: Mapped[list | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    id: Mapped[str] = mapped_column(String(96), primary_key=True)
    document_id: Mapped[str] = mapped_column(
        ForeignKey("knowledge_documents.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM))
    embedding_model: Mapped[str] = mapped_column(String(128))

    __table_args__ = (
        Index(
            "ix_knowledge_chunks_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )


class LLMCallLog(Base):
    """Metrics only — no prompt text, no user identifiers (privacy)."""

    __tablename__ = "llm_call_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    purpose: Mapped[str] = mapped_column(String(32))
    provider: Mapped[str] = mapped_column(String(32))
    model: Mapped[str] = mapped_column(String(128))
    mode: Mapped[str] = mapped_column(String(16))  # llm_grounded|rule_template
    fallback_reason: Mapped[str | None] = mapped_column(String(64))
    latency_ms: Mapped[float | None] = mapped_column(Float)
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    est_cost_usd: Mapped[float | None] = mapped_column(Float)
    grounded_ratio: Mapped[float | None] = mapped_column(Float)
    safe: Mapped[bool | None] = mapped_column(Boolean)
    rules_version: Mapped[str] = mapped_column(String(32))
