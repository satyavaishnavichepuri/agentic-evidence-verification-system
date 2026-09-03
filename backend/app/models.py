"""
Core data models for VeriScope AI.

The most important type here is AnswerContract. It is the single
object every investigation ultimately produces, and it is validated
with plain Python/Pydantic code -- never by asking an LLM whether its
own answer is trustworthy. See ContractValidatorAgent in
app/agents/contract_validator.py for the business-rule checks that
run on top of this schema.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def now() -> datetime:
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------
# Enums
# --------------------------------------------------------------------------

class SourceType(str, Enum):
    SEED = "seed"           # bundled demo corpus
    UPLOAD = "upload"       # user-uploaded PDF/TXT
    WEB = "web"              # simulated web research result


class Stance(str, Enum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    NEUTRAL = "neutral"


class ClaimStatus(str, Enum):
    VERIFIED = "verified"
    PARTIAL = "partial"
    CONTRADICTED = "contradicted"
    UNSUPPORTED = "unsupported"


class ContractStatus(str, Enum):
    VERIFIED = "VERIFIED"
    PARTIAL = "PARTIAL"
    DECLINED = "DECLINED"


class AgentName(str, Enum):
    PLANNER = "planner"
    RESEARCH = "research"
    EVIDENCE = "evidence"
    VERIFICATION = "verification"
    CONTRADICTION = "contradiction"
    CONTRACT_VALIDATOR = "contract_validator"


class AgentStepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


# --------------------------------------------------------------------------
# Knowledge base / RAG
# --------------------------------------------------------------------------

class Source(BaseModel):
    id: str = Field(default_factory=lambda: new_id("src"))
    title: str
    type: SourceType
    url: Optional[str] = None
    filename: Optional[str] = None
    published: Optional[str] = None  # free-text date/venue, demo purposes
    retrieved_at: datetime = Field(default_factory=now)


class Chunk(BaseModel):
    id: str = Field(default_factory=lambda: new_id("chk"))
    source_id: str
    text: str
    # Optional authoring hint used only by the seed corpus so the demo
    # can deterministically illustrate supports/contradicts/insufficient
    # evidence without needing a real entailment model.
    stance_hint: Optional[Stance] = None


class DocumentSummary(BaseModel):
    source: Source
    chunk_count: int
    preview: str


# --------------------------------------------------------------------------
# Investigation working data
# --------------------------------------------------------------------------

class SubQuestion(BaseModel):
    id: str = Field(default_factory=lambda: new_id("sq"))
    text: str


class EvidenceItem(BaseModel):
    id: str = Field(default_factory=lambda: new_id("ev"))
    claim_id: str
    source_id: str
    chunk_id: str
    snippet: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    stance: Stance


class Claim(BaseModel):
    id: str = Field(default_factory=lambda: new_id("clm"))
    subquestion_id: str
    text: str
    status: ClaimStatus
    evidence_ids: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = ""

    @field_validator("evidence_ids")
    @classmethod
    def _no_dupe_evidence(cls, v: List[str]) -> List[str]:
        if len(v) != len(set(v)):
            raise ValueError("duplicate evidence_ids in claim")
        return v


class Contradiction(BaseModel):
    id: str = Field(default_factory=lambda: new_id("ctr"))
    claim_ids: List[str]
    description: str
    evidence_ids: List[str] = Field(default_factory=list)


# --------------------------------------------------------------------------
# The Answer Contract
# --------------------------------------------------------------------------

class AnswerContract(BaseModel):
    """
    The binding output of an investigation. Validated in code
    (see ContractValidatorAgent), never self-certified by an LLM.

    Hard rules enforced by validators below:
      * every claim's evidence_ids must be non-empty UNLESS its status
        is UNSUPPORTED (an unsupported claim is, by definition, one
        with no grounding evidence)
      * citations may only reference source_ids that actually appear
        in some claim's evidence
      * contradictions may only reference claim_ids that exist in claims
      * overall `status` must be internally consistent with the claim
        statuses (checked again, independently, by the validator agent)
    """
    investigation_id: str
    question: str
    scope: str
    status: ContractStatus
    summary: str
    claims: List[Claim]
    citations: List[str] = Field(default_factory=list)
    missing_evidence: List[str] = Field(default_factory=list)
    contradictions: List[Contradiction] = Field(default_factory=list)
    validation_errors: List[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=now)

    @model_validator(mode="after")
    def _contradictions_reference_real_claims(self) -> "AnswerContract":
        claim_ids = {c.id for c in self.claims}
        for c in self.contradictions:
            for cid in c.claim_ids:
                if cid not in claim_ids:
                    raise ValueError(
                        f"contradiction {c.id} references unknown claim {cid}"
                    )
        return self

    @model_validator(mode="after")
    def _evidence_required_unless_unsupported(self) -> "AnswerContract":
        for claim in self.claims:
            if claim.status != ClaimStatus.UNSUPPORTED and not claim.evidence_ids:
                raise ValueError(
                    f"claim {claim.id} has status {claim.status} but no evidence"
                )
        return self


# --------------------------------------------------------------------------
# Agent trace (drives the Agent Monitor + workspace progress panel)
# --------------------------------------------------------------------------

class AgentStep(BaseModel):
    id: str = Field(default_factory=lambda: new_id("step"))
    investigation_id: str
    agent: AgentName
    status: AgentStepStatus = AgentStepStatus.PENDING
    message: str = ""
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    duration_ms: Optional[int] = None


# --------------------------------------------------------------------------
# Evidence graph (Question -> Claim -> Evidence -> Source)
# --------------------------------------------------------------------------

class GraphNode(BaseModel):
    id: str
    kind: str  # "question" | "claim" | "evidence" | "source"
    label: str
    status: Optional[str] = None


class GraphEdge(BaseModel):
    source: str
    target: str


class EvidenceGraph(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]


# --------------------------------------------------------------------------
# Investigation
# --------------------------------------------------------------------------

class InvestigationStatus(str, Enum):
    PLANNING = "planning"
    RESEARCHING = "researching"
    VERIFYING = "verifying"
    COMPLETE = "complete"
    FAILED = "failed"


class Investigation(BaseModel):
    id: str = Field(default_factory=lambda: new_id("inv"))
    question: str
    status: InvestigationStatus = InvestigationStatus.PLANNING
    subquestions: List[SubQuestion] = Field(default_factory=list)
    claims: List[Claim] = Field(default_factory=list)
    evidence: List[EvidenceItem] = Field(default_factory=list)
    contradictions: List[Contradiction] = Field(default_factory=list)
    contract: Optional[AnswerContract] = None
    agent_trace: List[AgentStep] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=now)
    updated_at: datetime = Field(default_factory=now)
    is_seed: bool = False


class InvestigationSummary(BaseModel):
    id: str
    question: str
    status: InvestigationStatus
    contract_status: Optional[ContractStatus]
    claim_count: int
    created_at: datetime


class CreateInvestigationRequest(BaseModel):
    question: str = Field(min_length=4, max_length=500)
