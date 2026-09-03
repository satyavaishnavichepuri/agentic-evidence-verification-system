"""
Orchestrator.

Runs the full pipeline for one investigation:

  Planner -> Research -> Evidence -> Verification -> Contradiction
  -> Contract Validator

and updates investigation.agent_trace as it goes so the Investigation
Workspace and Agent Monitor can show live progress. Designed to run
inside a FastAPI BackgroundTask.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone

from ..models import (
    AgentName,
    AgentStep,
    AgentStepStatus,
    Investigation,
    InvestigationStatus,
)
from ..storage import store
from . import contract_validator, contradiction, evidence, planner, research, verification

# small pacing delay so the live agent-progress UI is genuinely visible
# instead of flashing "done" instantly; keeps demos legible.
STEP_DELAY_SECONDS = 0.35


def _start_step(inv: Investigation, agent: AgentName, message: str) -> AgentStep:
    step = AgentStep(
        investigation_id=inv.id,
        agent=agent,
        status=AgentStepStatus.RUNNING,
        message=message,
        started_at=datetime.now(timezone.utc),
    )
    inv.agent_trace.append(step)
    store.save_investigation(inv)
    time.sleep(STEP_DELAY_SECONDS)
    return step


def _finish_step(inv: Investigation, step: AgentStep, message: str, failed: bool = False) -> None:
    step.status = AgentStepStatus.FAILED if failed else AgentStepStatus.DONE
    step.message = message
    step.finished_at = datetime.now(timezone.utc)
    if step.started_at:
        step.duration_ms = int((step.finished_at - step.started_at).total_seconds() * 1000)
    store.save_investigation(inv)


def run_investigation(investigation_id: str) -> None:
    inv = store.get_investigation(investigation_id)
    if inv is None:
        return

    try:
        # 1. Planner
        inv.status = InvestigationStatus.PLANNING
        step = _start_step(inv, AgentName.PLANNER, "Decomposing question into subquestions...")
        subquestions = planner.plan(inv.question)
        inv.subquestions = subquestions
        _finish_step(inv, step, f"Generated {len(subquestions)} subquestion(s).")

        # 2. Research / RAG
        inv.status = InvestigationStatus.RESEARCHING
        step = _start_step(inv, AgentName.RESEARCH, "Retrieving candidate evidence from corpus...")
        research_results = research.research(subquestions)
        total_hits = sum(len(v) for v in research_results.values())
        _finish_step(inv, step, f"Retrieved {total_hits} candidate chunk(s) across all subquestions.")

        # 3. Evidence
        step = _start_step(inv, AgentName.EVIDENCE, "Synthesizing claims and attaching evidence...")
        claims, evidence_items = evidence.build_claims_and_evidence(subquestions, research_results)
        inv.claims = claims
        inv.evidence = evidence_items
        _finish_step(inv, step, f"Drafted {len(claims)} claim(s) with {len(evidence_items)} evidence item(s).")

        # 4. Verification
        inv.status = InvestigationStatus.VERIFYING
        step = _start_step(inv, AgentName.VERIFICATION, "Classifying evidence stance and claim status...")
        claims_by_id = {c.id: c for c in claims}
        verification.classify_evidence_stances(evidence_items, claims_by_id)
        verification.finalize_claim_statuses(claims, evidence_items)
        statuses = ", ".join(f"{c.status.value}" for c in claims)
        _finish_step(inv, step, f"Statuses: {statuses}.")

        # 5. Contradiction
        step = _start_step(inv, AgentName.CONTRADICTION, "Scanning for conflicting evidence...")
        contradictions = contradiction.detect_contradictions(claims, evidence_items)
        inv.contradictions = contradictions
        _finish_step(inv, step, f"Found {len(contradictions)} contradiction(s).")

        # 6. Contract Validator
        step = _start_step(inv, AgentName.CONTRACT_VALIDATOR, "Validating Answer Contract against evidence rules...")
        contract = contract_validator.build_contract(
            inv.id, inv.question, claims, evidence_items, contradictions
        )
        inv.contract = contract
        inv.claims = claims  # evidence_ids may have been trimmed to "usable" set
        msg = f"Contract status: {contract.status.value}."
        if contract.validation_errors:
            msg += f" {len(contract.validation_errors)} validation error(s) -- forced DECLINED."
        _finish_step(inv, step, msg, failed=bool(contract.validation_errors))

        inv.status = InvestigationStatus.COMPLETE

    except Exception as exc:  # noqa: BLE001
        inv.status = InvestigationStatus.FAILED
        inv.agent_trace.append(
            AgentStep(
                investigation_id=inv.id,
                agent=AgentName.CONTRACT_VALIDATOR,
                status=AgentStepStatus.FAILED,
                message=f"Pipeline error: {exc}",
                started_at=datetime.now(timezone.utc),
                finished_at=datetime.now(timezone.utc),
            )
        )
    finally:
        inv.updated_at = datetime.now(timezone.utc)
        store.save_investigation(inv)
