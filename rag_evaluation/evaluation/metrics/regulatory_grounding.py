"""
Regulatory Grounding Score — custom DeepEval metric.

Measures whether the generated answer correctly cites or paraphrases a
regulation clause that is relevant to the question.

In a legal/regulatory RAG system (e.g. GDPR Q&A), retrieved passages
contain specific articles and recitals. An answer that is *faithful* to
the retrieved text still might not ground itself in the correct normative
clause. This metric specifically checks whether the answer:

    1. Identifies the right regulatory provision (article, paragraph, or
       recital) for the question asked.
    2. Correctly represents what that provision says — either through
       direct citation or accurate paraphrase.
    3. Does not misattribute content to the wrong article or confuse
       separate obligations.

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
METRIC_NAME = "regulatory_grounding"

_CRITERIA = (
    "Does the answer correctly cite or paraphrase a regulation clause "
    "that is relevant to the question? "
    "Award a high score when the answer accurately refers to a specific "
    "article, paragraph, or recital from the retrieved regulation text and "
    "correctly represents its content. "
    "Penalise answers that cite the wrong clause, misquote a provision, "
    "omit any clause reference entirely when one is clearly needed, or "
    "fabricate regulatory content not present in the retrieval context."
)

_EVALUATION_STEPS = [
    "Read the question and identify which regulatory provision (article, "
    "paragraph, recital, or clause) is most directly relevant.",
    "Check whether the answer references that provision by name, number, or "
    "accurate paraphrase.",
    "Verify that the characterisation of the provision is factually correct "
    "relative to the retrieval context provided.",
    "Penalise the answer if it cites the wrong article, distorts the "
    "meaning of the cited provision, or invents regulatory language not "
    "found in the retrieval context.",
    "Assign a score from 0 to 1: 1.0 = accurate citation/paraphrase of the "
    "correct clause; 0.5 = partially correct or missing clause number but "
    "semantically sound; 0.0 = wrong clause, fabricated content, or no "
    "regulatory grounding at all.",
]


def create_metric(
    model: str = "gpt-4o-mini",
    threshold: float = 0.7,
    **kwargs: Any,
) -> GEval:
    """Factory function to create a configured Regulatory Grounding metric.

    This is called by the metrics registry when instantiating metrics.

    Args:
        model: OpenAI model for LLM-as-judge evaluation.
        threshold: Minimum score (0-1) to consider a test case as passing.
            Defaults to 0.7.
        **kwargs: Additional keyword arguments (unused, for registry compat).

    Returns:
        A configured :class:`GEval` instance for regulatory grounding.
    """
    return GEval(
        name="Regulatory Grounding Score",
        criteria=_CRITERIA,
        evaluation_steps=_EVALUATION_STEPS,
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
            LLMTestCaseParams.RETRIEVAL_CONTEXT,
        ],
        threshold=threshold,
        model=model,
    )
