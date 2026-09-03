"""
Contradiction agent.

Scans the finalized claims/evidence for direct conflicts and produces
explicit Contradiction records the UI can render (right-hand panel of
the Workspace, and the evidence graph). Two kinds are detected:

  1. Intra-claim: a single claim has both supporting and contradicting
     evidence (status == CONTRADICTED).
  2. Cross-claim: two different claims cite evidence with opposite
     stances toward closely related subject matter -- detected via a
     lightweight lexical-overlap heuristic. This is a best-effort
     signal, not a full NLI system, and is documented as such.
"""
from __future__ import annotations

import re
from typing import List

from ..models import Claim, Contradiction, EvidenceItem, Stance

_STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "of", "to", "in", "on",
    "and", "or", "for", "does", "do", "did", "what", "that", "this", "with",
    "evidence", "available", "indicates", "no", "supporting", "found", "not",
}


def _keywords(text: str) -> set:
    words = re.findall(r"[a-zA-Z]{4,}", text.lower())
    return {w for w in words if w not in _STOPWORDS}


def detect_contradictions(
    claims: List[Claim], evidence: List[EvidenceItem]
) -> List[Contradiction]:
    contradictions: List[Contradiction] = []
    evidence_by_claim = {}
    for item in evidence:
        evidence_by_claim.setdefault(item.claim_id, []).append(item)

    # 1. Intra-claim contradictions
    for claim in claims:
        items = evidence_by_claim.get(claim.id, [])
        supports = [i for i in items if i.stance == Stance.SUPPORTS]
        contradicts = [i for i in items if i.stance == Stance.CONTRADICTS]
        if supports and contradicts:
            contradictions.append(
                Contradiction(
                    claim_ids=[claim.id],
                    description=(
                        "Sources disagree on this claim: "
                        f'"{claim.text}" -- {len(supports)} source(s) support it, '
                        f"{len(contradicts)} contradict it."
                    ),
                    evidence_ids=[i.id for i in supports + contradicts],
                )
            )

    # 2. Cross-claim contradictions: two different claims whose supporting
    #    evidence sets have opposite stances but overlap heavily in topic.
    claim_ids = [c.id for c in claims]
    for i in range(len(claim_ids)):
        for j in range(i + 1, len(claim_ids)):
            c1, c2 = claims[i], claims[j]
            kw1, kw2 = _keywords(c1.text), _keywords(c2.text)
            if not kw1 or not kw2:
                continue
            overlap = len(kw1 & kw2) / max(1, min(len(kw1), len(kw2)))
            if overlap < 0.4:
                continue
            items1 = evidence_by_claim.get(c1.id, [])
            items2 = evidence_by_claim.get(c2.id, [])
            stances1 = {i.stance for i in items1 if i.stance != Stance.NEUTRAL}
            stances2 = {i.stance for i in items2 if i.stance != Stance.NEUTRAL}
            if stances1 and stances2 and stances1.isdisjoint(stances2):
                contradictions.append(
                    Contradiction(
                        claim_ids=[c1.id, c2.id],
                        description=(
                            "These related claims are supported by evidence "
                            "pointing in opposite directions -- worth reviewing "
                            "together."
                        ),
                        evidence_ids=[i.id for i in items1 + items2],
                    )
                )

    return contradictions
