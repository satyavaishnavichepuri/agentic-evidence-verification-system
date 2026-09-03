"""
Contract Validator agent.

This is the enforcement point for VeriScope's core promise: the
Answer Contract is validated with code, not by asking the LLM to
grade its own work.

Two layers of checking:
  1. Pydantic schema validation (AnswerContract's field/model
     validators in app/models.py) -- structural correctness.
  2. Business-rule status derivation, done here in plain Python:
     the overall VERIFIED / PARTIAL / DECLINED status is computed
     deterministically from claim statuses, never asserted by an LLM.

If either layer fails, the contract is NOT discarded -- it is
downgraded to DECLINED, the validation errors are attached and shown
in the UI, and the investigation still completes. A validation
failure is itself a legitimate, visible outcome, not a crash.
"""
from __future__ import annotations

from typing import List

from pydantic import ValidationError

from ..models import (
    AnswerContract,
    Claim,
    ClaimStatus,
    ContractStatus,
    Contradiction,
    EvidenceItem,
    now,
)


def _derive_status(claims: List[Claim]) -> ContractStatus:
    if not claims:
        return ContractStatus.DECLINED

    verified = sum(1 for c in claims if c.status == ClaimStatus.VERIFIED)
    partial = sum(1 for c in claims if c.status == ClaimStatus.PARTIAL)
    contradicted = sum(1 for c in claims if c.status == ClaimStatus.CONTRADICTED)
    unsupported = sum(1 for c in claims if c.status == ClaimStatus.UNSUPPORTED)

    if verified == len(claims):
        return ContractStatus.VERIFIED

    usable = verified + partial
    if usable == 0:
        return ContractStatus.DECLINED

    if contradicted > 0 or unsupported > 0 or partial > 0:
        return ContractStatus.PARTIAL

    return ContractStatus.VERIFIED


def _build_summary(question: str, claims: List[Claim], status: ContractStatus) -> str:
    if status == ContractStatus.DECLINED:
        return (
            "VeriScope could not produce a sufficiently supported answer to "
            "this question. See 'Missing evidence' for what would be needed."
        )
    verified = [c for c in claims if c.status == ClaimStatus.VERIFIED]
    partial = [c for c in claims if c.status == ClaimStatus.PARTIAL]
    contradicted = [c for c in claims if c.status == ClaimStatus.CONTRADICTED]
    parts = []
    if verified:
        parts.append(f"{len(verified)} finding(s) are well-supported by evidence")
    if partial:
        parts.append(f"{len(partial)} finding(s) are only partially supported")
    if contradicted:
        parts.append(f"{len(contradicted)} finding(s) have conflicting evidence")
    detail = "; ".join(parts) if parts else "no findings met the evidence bar"
    prefix = "Findings are fully supported." if status == ContractStatus.VERIFIED else "Mixed result:"
    return f"{prefix} {detail}."


def build_contract(
    investigation_id: str,
    question: str,
    claims: List[Claim],
    evidence: List[EvidenceItem],
    contradictions: List[Contradiction],
) -> AnswerContract:
    status = _derive_status(claims)
    summary = _build_summary(question, claims, status)

    evidence_by_id = {e.id: e for e in evidence}
    citations = sorted({
        evidence_by_id[eid].source_id
        for c in claims
        for eid in c.evidence_ids
        if eid in evidence_by_id
    })
    missing_evidence = []
    for c in claims:
        if c.status == ClaimStatus.UNSUPPORTED:
            missing_evidence.append(
                f"No corpus evidence was found to answer this sub-question "
                f"(claim id {c.id}). Uploading a relevant document would let "
                f"VeriScope re-evaluate it."
            )
        elif c.status == ClaimStatus.PARTIAL:
            missing_evidence.append(
                f'Additional independent, high-relevance sources are needed to fully '
                f'verify: "{c.text}"'
            )

    scope = (
        f"This investigation covers {len(claims)} sub-question(s) derived from the "
        f"original question, answered strictly from the retrieved corpus "
        f"(seed knowledge base plus any uploaded documents). It does not draw on "
        f"outside knowledge beyond that corpus."
    )

    try:
        contract = AnswerContract(
            investigation_id=investigation_id,
            question=question,
            scope=scope,
            status=status,
            summary=summary,
            claims=claims,
            citations=citations,
            missing_evidence=missing_evidence,
            contradictions=contradictions,
            validation_errors=[],
        )
        return contract
    except ValidationError as exc:
        errors = [f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors()]
        # Degrade gracefully: still return a contract object, forced DECLINED,
        # with the concrete validation errors visible in the UI.
        safe_claims = [c for c in claims]  # keep for transparency even if invalid
        return AnswerContract.model_construct(
            investigation_id=investigation_id,
            question=question,
            scope=scope,
            status=ContractStatus.DECLINED,
            summary="Contract validation failed -- see validation errors below.",
            claims=safe_claims,
            citations=citations,
            missing_evidence=missing_evidence,
            contradictions=contradictions,
            validation_errors=errors,
            generated_at=now(),
        )
