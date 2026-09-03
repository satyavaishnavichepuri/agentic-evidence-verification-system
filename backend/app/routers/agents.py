from __future__ import annotations

from pydantic import BaseModel

from fastapi import APIRouter

from ..gemini_client import gemini_available
from ..config import settings
from ..models import AgentName, AgentStepStatus
from ..storage import store

router = APIRouter(prefix="/api/agents", tags=["agents"])


class AgentRunView(BaseModel):
    id: str
    investigation_id: str
    investigation_question: str
    agent: AgentName
    status: AgentStepStatus
    message: str
    started_at: str | None
    finished_at: str | None
    duration_ms: int | None


class AgentMonitorSummary(BaseModel):
    gemini_enabled: bool
    postgres_enabled: bool
    total_runs: int
    by_agent: dict[str, int]
    by_status: dict[str, int]


@router.get("/runs", response_model=list[AgentRunView])
def list_agent_runs():
    runs: list[AgentRunView] = []
    for inv in store.list_investigations():
        for step in inv.agent_trace:
            runs.append(
                AgentRunView(
                    id=step.id,
                    investigation_id=inv.id,
                    investigation_question=inv.question,
                    agent=step.agent,
                    status=step.status,
                    message=step.message,
                    started_at=step.started_at.isoformat() if step.started_at else None,
                    finished_at=step.finished_at.isoformat() if step.finished_at else None,
                    duration_ms=step.duration_ms,
                )
            )
    runs.sort(key=lambda r: r.started_at or "", reverse=True)
    return runs


@router.get("/status", response_model=AgentMonitorSummary)
def agent_status():
    by_agent: dict[str, int] = {}
    by_status: dict[str, int] = {}
    total = 0
    for inv in store.list_investigations():
        for step in inv.agent_trace:
            total += 1
            by_agent[step.agent.value] = by_agent.get(step.agent.value, 0) + 1
            by_status[step.status.value] = by_status.get(step.status.value, 0) + 1
    return AgentMonitorSummary(
        gemini_enabled=gemini_available(),
        postgres_enabled=settings.postgres_enabled,
        total_runs=total,
        by_agent=by_agent,
        by_status=by_status,
    )
