"""
Simple local RAG.

- Chunks plain text into overlapping windows.
- Indexes every chunk in the corpus (seed sources + uploaded docs)
  with TF-IDF and retrieves by cosine similarity.
- No external services required -- this is what makes "zero API keys,
  zero database setup" true for the research step, not just the UI.

The index is rebuilt whenever new chunks are added. That's O(n) work
on every upload, which is perfectly fine at demo/small-corpus scale
and keeps the implementation easy to reason about.
"""
from __future__ import annotations

from typing import List, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .models import Chunk
from .storage import store

CHUNK_SIZE = 480       # characters per chunk
CHUNK_OVERLAP = 80


def chunk_text(text: str) -> List[str]:
    text = " ".join(text.split())  # normalize whitespace
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        # try to break on a sentence/word boundary
        if end < len(text):
            boundary = text.rfind(". ", start, end)
            if boundary == -1 or boundary < start + 100:
                boundary = text.rfind(" ", start, end)
            if boundary > start:
                end = boundary + 1
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - CHUNK_OVERLAP, start + 1)
    return [c for c in chunks if c]


class RagIndex:
    """Thin wrapper that (re)builds a TF-IDF index over all stored chunks."""

    def __init__(self) -> None:
        self._vectorizer: TfidfVectorizer | None = None
        self._matrix = None
        self._chunk_ids: List[str] = []
        self._dirty = True

    def mark_dirty(self) -> None:
        self._dirty = True

    def _rebuild(self) -> None:
        chunks = store.list_chunks()
        self._chunk_ids = [c.id for c in chunks]
        texts = [c.text for c in chunks]
        if not texts:
            self._vectorizer = None
            self._matrix = None
            self._dirty = False
            return
        self._vectorizer = TfidfVectorizer(
            stop_words="english", ngram_range=(1, 2), max_features=8000
        )
        self._matrix = self._vectorizer.fit_transform(texts)
        self._dirty = False

    def search(self, query: str, top_k: int = 5) -> List[Tuple[Chunk, float]]:
        if self._dirty:
            self._rebuild()
        if self._vectorizer is None or self._matrix is None:
            return []
        q_vec = self._vectorizer.transform([query])
        sims = cosine_similarity(q_vec, self._matrix).flatten()
        order = np.argsort(-sims)[:top_k]
        chunks_by_id = {c.id: c for c in store.list_chunks()}
        results = []
        for idx in order:
            score = float(sims[idx])
            if score <= 0.0:
                continue
            chunk_id = self._chunk_ids[idx]
            chunk = chunks_by_id.get(chunk_id)
            if chunk:
                results.append((chunk, score))
        return results


rag_index = RagIndex()


def add_document_chunks(source_id: str, raw_text: str) -> List[Chunk]:
    pieces = chunk_text(raw_text)
    chunks = [Chunk(source_id=source_id, text=piece) for piece in pieces]
    store.save_chunks(chunks)
    rag_index.mark_dirty()
    return chunks


def add_seed_chunks(chunks: List[Chunk]) -> None:
    store.save_chunks(chunks)
    rag_index.mark_dirty()
