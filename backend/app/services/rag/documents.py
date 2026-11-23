"""Knowledge-base document model and chunking.

Only documents with verification_status == "verified" (a person checked the source and its
licence) may be ingested. Metadata travels with every chunk so citations always point to a
real, stored source — the system never invents citations.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Literal

SourceType = Literal["scientific", "dermatology_guideline", "ingredient_db", "manufacturer", "regulatory"]


@dataclass(frozen=True)
class SourceDocument:
    doc_id: str
    title: str
    source_type: SourceType
    source_url: str
    publisher: str
    accessed_at: date
    license: str
    verification_status: Literal["pending", "verified", "rejected"]
    language: str = "en"
    topics: tuple[str, ...] = ()  # e.g. needs or INCI names, used as retrieval filters


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    doc: SourceDocument
    text: str
    position: int


_SPLIT = re.compile(r"(?<=[.!?])\s+")


def chunk_text(
    doc: SourceDocument, text: str, max_chars: int = 800, overlap_sentences: int = 1
) -> list[Chunk]:
    """Paragraph-aware, sentence-boundary chunking with sentence overlap."""
    if max_chars < 100:
        raise ValueError("max_chars too small")
    sentences: list[str] = []
    for para in re.split(r"\n\s*\n", text):
        sentences.extend(s.strip() for s in _SPLIT.split(para.strip()) if s.strip())
    chunks: list[list[str]] = []
    cur: list[str] = []
    for s in sentences:
        if cur and len(" ".join(cur + [s])) > max_chars:
            chunks.append(cur)
            cur = cur[-overlap_sentences:] if overlap_sentences else []
        cur.append(s)
    if cur:
        chunks.append(cur)
    return [Chunk(f"{doc.doc_id}#{i}", doc, " ".join(c), i) for i, c in enumerate(chunks)]
