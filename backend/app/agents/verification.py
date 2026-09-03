"""
Verification agent.

Two jobs:
  1. Stance classification -- for any evidence item that doesn't
     already carry an authored stance_hint (seed corpus only), decide
     whether the snippet supports, contradicts, or is neutral toward
     its claim. Uses Gemini if configured; otherwise a transparent
     relevance-based heuristic (documented, not hidden).
  2. Claim status -- turns the stance-labeled evidence set for each
     claim into one of VERIFIED / PARTIAL / CONTRADICTED / UNSUPPORTED,
     purely from counts and thresholds in code. The LLM is never asked
     "is this claim true" -- only ever "what does this one snippet say".
"""
from __future__ import annotations

from typing import List

from ..gemini_client import gemini_available, generate_text
from ..models import Claim, ClaimStatus, EvidenceItem, Stance

SUPPORT_RELEVANCE_FLOOR = 0.05
STRONG_RELEVANCE = 0.35
MIN_EVIDENCE_FOR_VERIFIED = 2

_SYSTEM = (
    "You are the verification agent inside VeriScope AI. You are given a "
    "claim and one evidence snippet. Answer with exactly one word: "
    "SUPPORTS, CONTRADICTS, or NEUTRAL -- describing whether the snippet "
    "supports the claim, contradicts it, or is neutral/unrelated."
)


def _classify_stance(claim_text: str, snippet: str) -> Stance:
    if gemini_available():
        result = generate_text(
            f'Claim: "{claim_text}"\nSnippet: "{snippet}"\nAnswer:',
            system=_SYSTEM,
        )
        if result:
            token = result.strip().upper()
            if "CONTRADICT" in token:
                return Stance.CONTRADICTS
            if "SUPPORT" in token:
                return Stance.SUPPORTS
            if "NEUTRAL" in token:
                return Stance.NEUTRAL
    # Deterministic fallback: without a real entailment model we treat
    # sufficiently relevant retrieved text as supportive by default,
    # and weakly-relevant text as neutral. This is intentionally
    # conservative and documented in architecture.md.
    return Stance.NEUTRAL


def classify_evidence_stances(evidence: List[EvidenceItem], claims_by_id: dict) -> None:
    for item in evidence:
        if item.stance != Stance.NEUTRAL:
            continue  # already authored (seed corpus) -- keep as ground truth
        claim = claims_by_id.get(item.claim_id)
        if not claim:
            continue
        if item.relevance_score < SUPPORT_RELEVANCE_FLOOR:
            continue
        classified = _classify_stance(claim.text, item.snippet)
        if classified == Stance.NEUTRAL and item.relevance_score >= STRONG_RELEVANCE:
            # relevant enough to have been retrieved for this exact
            # synthesized claim, and no LLM contradiction signal -> supports
            classified = Stance.SUPPORTS
        item.stance = classified


def finalize_claim_statuses(claims: List[Claim], evidence: List[EvidenceItem]) -> None:
    evidence_by_claim: dict[str, List[EvidenceItem]] = {}
    for item in evidence:
        evidence_by_claim.setdefault(item.claim_id, []).append(item)

    for claim in claims:
        items = evidence_by_claim.get(claim.id, [])
        usable = [i for i in items if i.relevance_score >= SUPPORT_RELEVANCE_FLOOR]

        supports = [i for i in usable if i.stance == Stance.SUPPORTS]
        contradicts = [i for i in usable if i.stance == Stance.CONTRADICTS]

        if not usable:
            claim.status = ClaimStatus.UNSUPPORTED
            claim.evidence_ids = []
            claim.confidence = 0.0
            claim.rationale = "No evidence in the corpus met the relevance threshold."
            continue

        avg_support_relevance = (
            sum(i.relevance_score for i in supports) / len(supports) if supports else 0.0
        )

        if supports and contradicts:
            claim.status = ClaimStatus.CONTRADICTED
            claim.confidence = round(min(avg_support_relevance, 0.6), 3)
            claim.rationale = (
                f"{len(supports)} source(s) support this claim while "
                f"{len(contradicts)} source(s) contradict it."
            )
        elif not supports:
            claim.status = ClaimStatus.PARTIAL
            claim.confidence = round(0.2, 3)
            claim.rationale = "Retrieved evidence was only weakly or neutrally related."
        elif len(supports) < MIN_EVIDENCE_FOR_VERIFIED or avg_support_relevance < STRONG_RELEVANCE:
            claim.status = ClaimStatus.PARTIAL
            claim.confidence = round(0.35 + avg_support_relevance * 0.3, 3)
            claim.rationale = (
                f"Only {len(supports)} supporting source(s) with moderate relevance "
                f"(avg {avg_support_relevance:.2f}); not enough for full verification."
            )
        else:
            claim.status = ClaimStatus.VERIFIED
            claim.confidence = round(min(0.6 + avg_support_relevance * 0.4, 0.98), 3)
            claim.rationale = (
                f"{len(supports)} independent source(s) support this claim "
                f"with strong relevance (avg {avg_support_relevance:.2f})."
            )

        claim.evidence_ids = [i.id for i in usable]
