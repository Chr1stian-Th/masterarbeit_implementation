"""
Legal Interpretability — custom DeepEval metric.

Measures whether the generated answer is legally clear, accurate in its
interpretation, and understandable to a non-specialist reader who is
consulting the regulation.

Faithfulness and regulatory grounding check *what* is said; legal
interpretability checks *how well* it is communicated in a legal context.
A high score requires the answer to:

    1. Use legally precise language without introducing ambiguity.
    2. Correctly interpret the normative meaning of the cited provision
       (obligations vs. permissions, data subject rights vs. controller
       duties, etc.).
    3. Be structured and phrased so that a reader with no legal background
       can act on the information.
    4. Avoid misleading simplifications or over-broad generalisations that
       could cause a reader to misapply the regulation.

Implementation uses DeepEval's ``GEval`` (G-Eval) framework, which
instructs an LLM judge to score the answer on a 0–1 scale using
chain-of-thought evaluation steps.

Adding this metric:
    This module is automatically discovered by the metrics registry.
    No additional registration is needed.

See Also:
    - `DeepEval GEval Docs <https://docs.confident-ai.com/docs/metrics-llm-evals>`_
"""

from __future__ import annotations

from typing import Any

from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCaseParams


# Metric identifier used by the registry
METRIC_NAME = "legal_interpretability"

_CRITERIA = (
    "Is the answer legally clear, accurate in its interpretation, and "
    "understandable to someone reading the regulation? "
    "A high-scoring answer uses precise legal language, correctly interprets "
    "the normative force of the provision (e.g. obligation vs. permission, "
    "right vs. duty), and is phrased so that a non-specialist reader can "
    "understand and act on it. "
    "Penalise answers that introduce legal ambiguity, mischaracterise "
    "obligations as permissions (or vice versa), use jargon without "
    "explanation, or oversimplify in ways that could mislead the reader."
)

_EVALUATION_STEPS = [
    "Read the question to understand what legal information the user needs.",
    "Assess whether the answer uses accurate legal terminology and correctly "
    "distinguishes between obligations, prohibitions, and permissions.",
    "Check whether the normative interpretation is correct: does the answer "
    "accurately convey who must do what, under which conditions, and with "
    "what exceptions?",
    "Evaluate clarity: could a non-specialist reader understand the answer "
    "and know how to act on it without further legal advice?",
    "Identify any misleading simplifications, missing qualifications, or "
    "ambiguous phrasing that could cause the reader to misapply the "
    "regulation.",
    "Assign a score from 0 to 1: 1.0 = legally precise, correctly "
    "interpreted, and clearly understandable; 0.5 = mostly correct but "
    "with minor clarity or precision issues; 0.0 = legally inaccurate, "
    "misleading, or incomprehensible.",
]


def create_metric(
    model: str = "gpt-4o-mini",
    threshold: float = 0.7,
    **kwargs: Any,
) -> GEval:
    """Factory function to create a configured Legal Interpretability metric.

    This is called by the metrics registry when instantiating metrics.

    Args:
        model: OpenAI model for LLM-as-judge evaluation.
        threshold: Minimum score (0-1) to consider a test case as passing.
            Defaults to 0.7.
        **kwargs: Additional keyword arguments (unused, for registry compat).

    Returns:
        A configured :class:`GEval` instance for legal interpretability.
    """
    return GEval(
        name="Legal Interpretability",
        criteria=_CRITERIA,
        evaluation_steps=_EVALUATION_STEPS,
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
        ],
        threshold=threshold,
        model=model,
    )
