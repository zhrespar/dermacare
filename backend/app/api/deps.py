"""Shared dependencies: DB session, current user, RAG retriever and LLM provider."""

import uuid
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import User
from app.services.llm import LLMProvider, build_provider
from app.services.rag import InMemoryVectorStore, PgVectorStore, Retriever, build_embedder

DB = Annotated[Session, Depends(get_db)]
_bearer = HTTPBearer(auto_error=False)
Creds = Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]


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


def _user_from(creds: HTTPAuthorizationCredentials | None, db: Session) -> User | None:
    if creds is None:
        return None
    uid: uuid.UUID | None = decode_access_token(creds.credentials)
    user = db.get(User, uid) if uid else None
    if user is None or not user.is_active or user.deleted_at is not None:
        return None
    return user


def get_current_user(db: DB, creds: Creds) -> User:
    user = _user_from(creds, db)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "not_authenticated")
    return user


def get_optional_user(db: DB, creds: Creds) -> User | None:
    return _user_from(creds, db)


CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]
