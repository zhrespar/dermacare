"""Shared dependencies: the RAG retriever and LLM provider, built from settings."""

from functools import lru_cache

from app.core.config import get_settings
from app.services.llm import LLMProvider, build_provider
from app.services.rag import InMemoryVectorStore, PgVectorStore, Retriever, build_embedder


@lru_cache
def get_retriever() -> Retriever:
    s = get_settings()
    emb = build_embedder(s.rag_embedding_backend, s.rag_embedding_model, s.rag_embedding_dim)
    if s.rag_store == "pgvector":
        from app.db.session import SessionLocal

        store = PgVectorStore(SessionLocal)
    else:
        store = InMemoryVectorStore()  # empty until verified sources are ingested
    return Retriever(emb, store, s.rag_top_k, s.rag_min_score)


def get_llm_provider() -> LLMProvider:
    return build_provider(get_settings())
