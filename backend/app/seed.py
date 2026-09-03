"""
Seeds VeriScope with a demo knowledge base and one fully pre-computed
demo investigation, so the entire workflow -- including a VERIFIED
claim, a PARTIAL claim, a CONTRADICTED claim, and an UNSUPPORTED
claim feeding a DECLINED-eligible path -- is visible with zero API
keys and zero setup.

The demo question: "Does intermittent fasting improve long-term
cardiovascular health outcomes?" -- a realistic research question
where real literature genuinely is mixed, which is exactly the
scenario VeriScope is built to handle honestly.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .agents import contract_validator, contradiction as contradiction_agent
from .models import (
    AgentName,
    AgentStep,
    AgentStepStatus,
    Chunk,
    Claim,
    ClaimStatus,
    EvidenceItem,
    Investigation,
    InvestigationStatus,
    Source,
    SourceType,
    Stance,
    SubQuestion,
)
from .rag import add_seed_chunks
from .storage import store

SEED_MARKER = "__veriscope_seeded__"


def _mins_ago(n: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(minutes=n)


def seed_knowledge_base() -> dict[str, Source]:
    sources_data = [
        dict(
            id="src_metaanalysis01",
            title="Meta-analysis: Intermittent Fasting and Cardiometabolic Risk (2023)",
            type=SourceType.SEED,
            url="https://example-journal.org/if-cardiometabolic-2023",
            published="Journal of Metabolic Research, 2023",
            text=(
                "A meta-analysis of 27 randomized controlled trials found that intermittent "
                "fasting protocols, including 16:8 time-restricted eating, produced statistically "
                "significant reductions in LDL cholesterol and systolic blood pressure over "
                "12-month follow-up periods compared to control diets. The effect size was "
                "moderate but consistent across trial sites, and researchers concluded that "
                "intermittent fasting is associated with measurable long-term cardiovascular "
                "risk factor improvement in overweight adults."
            ),
            stance=Stance.SUPPORTS,
        ),
        dict(
            id="src_cohort02",
            title="10-Year Cohort Study on Time-Restricted Eating (2022)",
            type=SourceType.SEED,
            url="https://example-journal.org/tre-cohort-2022",
            published="Cardiovascular Epidemiology Quarterly, 2022",
            text=(
                "In a prospective cohort of 3,400 adults followed for ten years, participants "
                "practicing consistent time-restricted eating showed a 14% lower incidence of "
                "major adverse cardiovascular events compared to matched controls, even after "
                "adjusting for baseline BMI, smoking status, and physical activity. The authors "
                "note the cohort was observational and cannot fully rule out confounding, but "
                "the association with reduced cardiovascular events remained robust across "
                "sensitivity analyses."
            ),
            stance=Stance.SUPPORTS,
        ),
        dict(
            id="src_rct03",
            title="Randomized Trial: No Cardiovascular Benefit from Alternate-Day Fasting (2024)",
            type=SourceType.WEB,
            url="https://example-medresearch.org/adf-null-result-2024",
            published="Clinical Nutrition Trials, 2024",
            text=(
                "This 18-month randomized controlled trial compared alternate-day fasting "
                "against standard caloric restriction in 512 participants with elevated "
                "cardiovascular risk. Contrary to earlier observational findings, the trial "
                "found no statistically significant difference in major adverse cardiovascular "
                "events, LDL cholesterol, or arterial stiffness between groups. The authors "
                "explicitly caution that intermittent fasting shows no clear long-term "
                "cardiovascular advantage over simple calorie reduction in this population."
            ),
            stance=Stance.CONTRADICTS,
        ),
        dict(
            id="src_review04",
            title="Narrative Review: Mechanisms of Fasting-Induced Metabolic Change (2021)",
            type=SourceType.SEED,
            url="https://example-journal.org/fasting-mechanisms-2021",
            published="Metabolism Reviews, 2021",
            text=(
                "Fasting periods trigger a metabolic switch from glucose to ketone body "
                "utilization, which is associated with reduced oxidative stress markers and "
                "improved insulin sensitivity in short-term studies. However, this review notes "
                "that most mechanistic evidence comes from studies lasting 8-12 weeks, and "
                "long-term human cardiovascular outcome data remains comparatively sparse."
            ),
            stance=Stance.NEUTRAL,
        ),
        dict(
            id="src_safety05",
            title="Safety Profile of Extended Fasting Protocols in Older Adults (2020)",
            type=SourceType.SEED,
            url="https://example-journal.org/if-safety-older-adults-2020",
            published="Geriatric Nutrition Letters, 2020",
            text=(
                "Extended fasting protocols in adults over 65 were associated with increased "
                "risk of hypoglycemia and muscle mass loss when not medically supervised. "
                "The study recommends caution and individualized medical guidance before "
                "recommending intermittent fasting to elderly populations, particularly those "
                "on glucose-lowering medication."
            ),
            stance=Stance.NEUTRAL,
        ),
        dict(
            id="src_editorial06",
            title="Editorial: Diet Trends and Publication Bias in Nutrition Science",
            type=SourceType.WEB,
            url="https://example-medresearch.org/nutrition-publication-bias",
            published="Nutrition Science Commentary, 2023",
            text=(
                "This editorial discusses general concerns about publication bias in "
                "popular-diet nutrition research and calls for larger, pre-registered trials "
                "across dietary intervention studies. It does not present new primary data on "
                "any specific fasting protocol."
            ),
            stance=Stance.NEUTRAL,
        ),
    ]

    created: dict[str, Source] = {}
    for data in sources_data:
        source = Source(
            id=data["id"],
            title=data["title"],
            type=data["type"],
            url=data["url"],
            published=data["published"],
            retrieved_at=_mins_ago(60),
        )
        store.save_source(source)
        chunk = Chunk(
            id=f"chk_{data['id']}",
            source_id=source.id,
            text=data["text"],
            stance_hint=data["stance"],
        )
        add_seed_chunks([chunk])
        created[source.id] = source
    return created


def seed_demo_investigation() -> Investigation:
    question = "Does intermittent fasting improve long-term cardiovascular health outcomes?"

    sq1 = SubQuestion(id="sq_demo_1", text="What direct evidence links intermittent fasting to improved cardiovascular risk factors?")
    sq2 = SubQuestion(id="sq_demo_2", text="Do long-term trials confirm reduced cardiovascular events from intermittent fasting?")
    sq3 = SubQuestion(id="sq_demo_3", text="What mechanisms are proposed to explain fasting's cardiovascular effects?")
    sq4 = SubQuestion(id="sq_demo_4", text="Is intermittent fasting safe and well-studied across all age groups long-term?")
    subquestions = [sq1, sq2, sq3, sq4]

    # Claim 1 -- VERIFIED: strong, consistent supporting evidence
    claim1 = Claim(
        id="clm_demo_verified",
        subquestion_id=sq1.id,
        text="Meta-analytic evidence indicates intermittent fasting produces measurable improvements in LDL cholesterol and blood pressure over 12 months.",
        status=ClaimStatus.VERIFIED,
        evidence_ids=["ev_demo_1"],
        confidence=0.89,
        rationale="1 independent source(s) support this claim with strong relevance (avg 0.91).",
    )
    ev1 = EvidenceItem(
        id="ev_demo_1",
        claim_id=claim1.id,
        source_id="src_metaanalysis01",
        chunk_id="chk_src_metaanalysis01",
        snippet="A meta-analysis of 27 randomized controlled trials found that intermittent fasting protocols produced statistically significant reductions in LDL cholesterol and systolic blood pressure over 12-month follow-up periods.",
        relevance_score=0.91,
        stance=Stance.SUPPORTS,
    )

    # Claim 2 -- CONTRADICTED: cohort study says yes, RCT says no
    claim2 = Claim(
        id="clm_demo_contradicted",
        subquestion_id=sq2.id,
        text="Long-term trial evidence is mixed on whether intermittent fasting reduces major adverse cardiovascular events.",
        status=ClaimStatus.CONTRADICTED,
        evidence_ids=["ev_demo_2", "ev_demo_3"],
        confidence=0.52,
        rationale="1 source(s) support this claim while 1 source(s) contradict it.",
    )
    ev2 = EvidenceItem(
        id="ev_demo_2",
        claim_id=claim2.id,
        source_id="src_cohort02",
        chunk_id="chk_src_cohort02",
        snippet="Participants practicing consistent time-restricted eating showed a 14% lower incidence of major adverse cardiovascular events compared to matched controls over ten years.",
        relevance_score=0.88,
        stance=Stance.SUPPORTS,
    )
    ev3 = EvidenceItem(
        id="ev_demo_3",
        claim_id=claim2.id,
        source_id="src_rct03",
        chunk_id="chk_src_rct03",
        snippet="This 18-month randomized controlled trial found no statistically significant difference in major adverse cardiovascular events between alternate-day fasting and standard caloric restriction.",
        relevance_score=0.85,
        stance=Stance.CONTRADICTS,
    )

    # Claim 3 -- PARTIAL: mechanistic plausibility but sparse long-term data
    claim3 = Claim(
        id="clm_demo_partial",
        subquestion_id=sq3.id,
        text="Fasting-induced metabolic switching is plausibly linked to cardiovascular benefit, but long-term human outcome data remains limited.",
        status=ClaimStatus.PARTIAL,
        evidence_ids=["ev_demo_4"],
        confidence=0.41,
        rationale="Only 1 supporting source(s) with moderate relevance (avg 0.34); not enough for full verification.",
    )
    ev4 = EvidenceItem(
        id="ev_demo_4",
        claim_id=claim3.id,
        source_id="src_review04",
        chunk_id="chk_src_review04",
        snippet="Fasting periods trigger a metabolic switch associated with reduced oxidative stress and improved insulin sensitivity, but long-term human cardiovascular outcome data remains comparatively sparse.",
        relevance_score=0.34,
        stance=Stance.SUPPORTS,
    )

    # Claim 4 -- UNSUPPORTED: corpus has nothing on cross-age-group long-term safety consensus
    claim4 = Claim(
        id="clm_demo_unsupported",
        subquestion_id=sq4.id,
        text="No corpus evidence establishes long-term safety consensus for intermittent fasting across all age groups.",
        status=ClaimStatus.UNSUPPORTED,
        evidence_ids=[],
        confidence=0.0,
        rationale="No evidence in the corpus met the relevance threshold for a cross-age-group long-term safety consensus.",
    )

    claims = [claim1, claim2, claim3, claim4]
    evidence = [ev1, ev2, ev3, ev4]
    contradictions = contradiction_agent.detect_contradictions(claims, evidence)
    contract = contract_validator.build_contract(
        "inv_demo_fasting", question, claims, evidence, contradictions
    )

    trace = []
    agents_seq = [
        (AgentName.PLANNER, f"Generated {len(subquestions)} subquestion(s)."),
        (AgentName.RESEARCH, "Retrieved 6 candidate chunk(s) across all subquestions."),
        (AgentName.EVIDENCE, f"Drafted {len(claims)} claim(s) with {len(evidence)} evidence item(s)."),
        (AgentName.VERIFICATION, "Statuses: verified, contradicted, partial, unsupported."),
        (AgentName.CONTRADICTION, f"Found {len(contradictions)} contradiction(s)."),
        (AgentName.CONTRACT_VALIDATOR, f"Contract status: {contract.status.value}."),
    ]
    base_time = _mins_ago(12)
    for i, (agent, msg) in enumerate(agents_seq):
        started = base_time + timedelta(seconds=i * 8)
        finished = started + timedelta(seconds=3)
        trace.append(
            AgentStep(
                id=f"step_demo_{i}",
                investigation_id="inv_demo_fasting",
                agent=agent,
                status=AgentStepStatus.DONE,
                message=msg,
                started_at=started,
                finished_at=finished,
                duration_ms=3000,
            )
        )

    inv = Investigation(
        id="inv_demo_fasting",
        question=question,
        status=InvestigationStatus.COMPLETE,
        subquestions=subquestions,
        claims=claims,
        evidence=evidence,
        contradictions=contradictions,
        contract=contract,
        agent_trace=trace,
        created_at=base_time,
        updated_at=base_time + timedelta(seconds=50),
        is_seed=True,
    )
    store.save_investigation(inv)
    return inv


def seed_declined_investigation() -> Investigation:
    """A second demo investigation illustrating a full DECLINED contract:
    the question is outside the corpus entirely, so every claim comes
    back unsupported and the contract is honestly declined rather than
    guessed at."""
    question = "What is the long-term cardiovascular safety of a specific unapproved experimental peptide, BPC-X9?"
    sq1 = SubQuestion(id="sq_decl_1", text="Is there any clinical trial data on BPC-X9 and cardiovascular outcomes?")
    sq2 = SubQuestion(id="sq_decl_2", text="Have any regulatory bodies published safety findings on BPC-X9?")

    claim1 = Claim(
        id="clm_decl_1",
        subquestion_id=sq1.id,
        text="No corpus evidence discusses BPC-X9 or its cardiovascular effects.",
        status=ClaimStatus.UNSUPPORTED,
        evidence_ids=[],
        confidence=0.0,
        rationale="No evidence in the corpus met the relevance threshold.",
    )
    claim2 = Claim(
        id="clm_decl_2",
        subquestion_id=sq2.id,
        text="No corpus evidence discusses regulatory findings on BPC-X9.",
        status=ClaimStatus.UNSUPPORTED,
        evidence_ids=[],
        confidence=0.0,
        rationale="No evidence in the corpus met the relevance threshold.",
    )
    claims = [claim1, claim2]
    evidence: list[EvidenceItem] = []
    contradictions = contradiction_agent.detect_contradictions(claims, evidence)
    contract = contract_validator.build_contract(
        "inv_demo_declined", question, claims, evidence, contradictions
    )

    base_time = _mins_ago(35)
    agents_seq = [
        (AgentName.PLANNER, "Generated 2 subquestion(s)."),
        (AgentName.RESEARCH, "Retrieved 0 candidate chunk(s) across all subquestions."),
        (AgentName.EVIDENCE, "Drafted 2 claim(s) with 0 evidence item(s)."),
        (AgentName.VERIFICATION, "Statuses: unsupported, unsupported."),
        (AgentName.CONTRADICTION, "Found 0 contradiction(s)."),
        (AgentName.CONTRACT_VALIDATOR, f"Contract status: {contract.status.value}."),
    ]
    trace = []
    for i, (agent, msg) in enumerate(agents_seq):
        started = base_time + timedelta(seconds=i * 6)
        finished = started + timedelta(seconds=2)
        trace.append(
            AgentStep(
                id=f"step_decl_{i}",
                investigation_id="inv_demo_declined",
                agent=agent,
                status=AgentStepStatus.DONE,
                message=msg,
                started_at=started,
                finished_at=finished,
                duration_ms=2000,
            )
        )

    inv = Investigation(
        id="inv_demo_declined",
        question=question,
        status=InvestigationStatus.COMPLETE,
        subquestions=[sq1, sq2],
        claims=claims,
        evidence=evidence,
        contradictions=contradictions,
        contract=contract,
        agent_trace=trace,
        created_at=base_time,
        updated_at=base_time + timedelta(seconds=40),
        is_seed=True,
    )
    store.save_investigation(inv)
    return inv


def run_seed() -> None:
    if store.list_sources():
        return  # already seeded (e.g. hot reload)
    seed_knowledge_base()
    seed_demo_investigation()
    seed_declined_investigation()
    print("[veriscope] Seed knowledge base + demo investigations loaded.")
