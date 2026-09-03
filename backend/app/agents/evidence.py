"""
Evidence agent.

Consumes the research agent's retrieved chunks and produces, per
subquestion:
  - a single candidate Claim (a proposed answer to that subquestion)
  - a list of EvidenceItem records grounding that claim in specific
    source chunks

The claim text itself is only ever derived from retrieved chunks --
if nothing relevant was retrieved, the claim is explicitly marked as
unsupported rather than invented. If Gemini is configured it is used
to phrase a tighter one-sentence claim from the retrieved snippets;
otherwise a deterministic heuristic builds the claim from the
top-scoring chunk. Either way, evidence attachment (which chunks
ground the claim) is computed in code, not by the LLM.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from ..gemini_client import gemini_available, generate_text
from ..models import Chunk, Claim, ClaimStatus, EvidenceItem, Stance, SubQuestion

RELEVANCE_FLOOR = 0.05  # below this, a chunk isn't considered real evidence

_SYSTEM = (
    "You are the evidence-synthesis agent inside VeriScope AI. You are given "
    "a subquestion and several retrieved text snippets. Write ONE concise "
    "sentence that states what the snippets, taken together, indicate about "
    "the subquestion. Only state what the snippets actually support -- do "
    "not add outside knowledge or speculation. If the snippets disagree with "
    "each other, say so plainly in the sentence."
)


def _heuristic_claim_text(subquestion: str, top_chunk_text: str) -> str:
    snippet = top_chunk_text.strip()
    if len(snippet) > 180:
        snippet = snippet[:177].rsplit(" ", 1)[0] + "..."
    return f"Available evidence indicates: {snippet}"


def _synthesize_claim_text(subquestion: str, hits: List[Tuple[Chunk, float]]) -> str:
    if not hits:
        return f"No supporting evidence was found for: {subquestion}"

    if gemini_available():
        joined = "\n".join(f"- {c.text}" for c, _ in hits[:4])
        result = generate_text(
            f'Subquestion: "{subquestion}"\n\nRetrieved snippets:\n{joined}\n\n'
            "One-sentence synthesis:",
            system=_SYSTEM,
        )
        if result:
            return result.strip().strip('"')

    return _heuristic_claim_text(subquestion, hits[0][0].text)


def build_claims_and_evidence(
    subquestions: List[SubQuestion],
    research_results: Dict[str, List[Tuple[Chunk, float]]],
) -> Tuple[List[Claim], List[EvidenceItem]]:
    claims: List[Claim] = []
    evidence: List[EvidenceItem] = []

    for sq in subquestions:
        hits = [h for h in research_results.get(sq.id, []) if h[1] >= RELEVANCE_FLOOR]
        claim_text = _synthesize_claim_text(sq.text, hits)

        claim = Claim(
            subquestion_id=sq.id,
            text=claim_text,
            status=ClaimStatus.UNSUPPORTED,  # verification agent will finalize
            evidence_ids=[],
            confidence=0.0,
        )

        for chunk, score in hits:
            item = EvidenceItem(
                claim_id=claim.id,
                source_id=chunk.source_id,
                chunk_id=chunk.id,
                snippet=chunk.text,
                relevance_score=round(min(score * 2.2, 1.0), 3),  # normalize TF-IDF scale
                stance=chunk.stance_hint or Stance.NEUTRAL,
            )
            evidence.append(item)
            claim.evidence_ids.append(item.id)

        claims.append(claim)

    return claims, evidence
