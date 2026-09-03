"""
Planner agent.

Turns the user's question into a small set of concrete subquestions
that the research/evidence/verification pipeline will answer
independently. Uses Gemini if configured to get sharper decomposition;
always has a deterministic fallback so demo mode works with zero keys.
"""
from __future__ import annotations

from typing import List

from ..gemini_client import gemini_available, generate_json
from ..models import SubQuestion

_SYSTEM = (
    "You are the planning agent inside VeriScope AI, a research-verification "
    "system. Break the user's question into 3-5 focused, independently "
    "answerable subquestions that together cover the scope of the original "
    "question. Include at least one subquestion that probes for "
    "counter-evidence or limitations."
)


def _fallback_subquestions(question: str) -> List[str]:
    q = question.strip().rstrip("?")
    return [
        f"What direct evidence exists regarding: {q}?",
        f"What is the strength and consistency of that evidence?",
        f"Is there any evidence that contradicts or complicates: {q}?",
        f"What relevant evidence, if any, is missing or unavailable?",
    ]


def plan(question: str) -> List[SubQuestion]:
    texts: List[str] = []
    if gemini_available():
        result = generate_json(
            f'User question: "{question}"\n\n'
            'Return a JSON array of 3-5 short subquestion strings. '
            'Example: ["...", "...", "..."]',
            system=_SYSTEM,
        )
        if isinstance(result, list):
            texts = [str(t).strip() for t in result if str(t).strip()][:5]

    if not texts:
        texts = _fallback_subquestions(question)

    return [SubQuestion(text=t) for t in texts]
