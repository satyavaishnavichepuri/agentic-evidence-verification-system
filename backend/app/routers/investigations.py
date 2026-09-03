from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, HTTPException

from ..agents.orchestrator import run_investigation
from ..graph import build_evidence_graph
from ..models import (
    CreateInvestigationRequest,
    EvidenceGraph,
    Investigation,
    InvestigationSummary,
)
from ..storage import store

router = APIRouter(prefix="/api/investigations", tags=["investigations"])


@router.post("", response_model=Investigation, status_code=201)
def create_investigation(payload: CreateInvestigationRequest, background_tasks: BackgroundTasks):
    inv = Investigation(question=payload.question.strip())
    store.save_investigation(inv)
    background_tasks.add_task(run_investigation, inv.id)
    return inv


@router.get("", response_model=list[InvestigationSummary])
def list_investigations():
    items = store.list_investigations()
    return [
        InvestigationSummary(
            id=i.id,
            question=i.question,
            status=i.status,
            contract_status=i.contract.status if i.contract else None,
            claim_count=len(i.claims),
            created_at=i.created_at,
        )
        for i in items
    ]


@router.get("/{investigation_id}", response_model=Investigation)
def get_investigation(investigation_id: str):
    inv = store.get_investigation(investigation_id)
    if inv is None:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return inv


@router.get("/{investigation_id}/graph", response_model=EvidenceGraph)
def get_investigation_graph(investigation_id: str):
    inv = store.get_investigation(investigation_id)
    if inv is None:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return build_evidence_graph(inv)
