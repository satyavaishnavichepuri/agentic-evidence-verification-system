"""
Research / RAG agent.

For each subquestion, retrieves the top matching chunks from the
local corpus (seed sources + anything the user has uploaded to the
Knowledge Base). This is the only place the pipeline "goes looking"
for information -- everything downstream only ever reasons about
what this agent actually retrieved.

Note on "web research": VeriScope's demo/local mode does not call an
external search API (that would break the zero-API-key guarantee).
Seed sources tagged type=web simulate previously-retrieved web
research so the workflow and UI are fully exercised. Wiring a real
search API is a documented extension point (see architecture.md).
"""
from __future__ import annotations

from typing import Dict, List

from ..models import Chunk, SubQuestion
from ..rag import rag_index

TOP_K = 4
MIN_RESULTS_TO_CONSIDER_FOUND = 1


def research(subquestions: List[SubQuestion]) -> Dict[str, List[tuple[Chunk, float]]]:
    """Returns {subquestion_id: [(chunk, score), ...]} ordered by relevance."""
    results: Dict[str, List[tuple[Chunk, float]]] = {}
    for sq in subquestions:
        hits = rag_index.search(sq.text, top_k=TOP_K)
        results[sq.id] = hits
    return results
