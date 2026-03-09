"""
Answer Relevancy metric implementation using DeepEval.

Answer Relevancy measures whether the generated answer actually addresses
the question that was asked. A faithful answer that stays grounded in the
retrieved context can still score poorly here if it answers a different
question or includes large amounts of irrelevant information.

DeepEval's ``AnswerRelevancyMetric`` uses an LLM-as-judge approach:

1. Extract statements from the generated answer.
2. For each statement, determine whether it is relevant to the input question.
3. Compute the relevancy score as the ratio of relevant statements.

Adding this metric:
    This module is automatically discovered by the metrics registry.
    No additional registration is needed.

See Also:
    - `DeepEval Answer Relevancy Docs <https://docs.confident-ai.com/docs/metrics-answer-relevancy>`_
"""

from __future__ import annotations

from typing import Any

from deepeval.metrics import AnswerRelevancyMetric


# Metric identifier used by the registry
METRIC_NAME = "answer_relevancy"


def create_metric(
    model: str = "gpt-4o-mini",
    threshold: float = 0.7,
    **kwargs: Any,
) -> AnswerRelevancyMetric:
    """Factory function to create a configured AnswerRelevancyMetric.

    This is called by the metrics registry when instantiating metrics.

    Args:
        model: OpenAI model for LLM-as-judge evaluation.
        threshold: Minimum score (0-1) to consider a test case as passing.
            Defaults to 0.7 (70% of answer statements must be relevant).
        **kwargs: Additional keyword arguments (unused, for registry compat).

    Returns:
        A configured :class:`AnswerRelevancyMetric` instance.
    """
    return AnswerRelevancyMetric(
        threshold=threshold,
        model=model,
        include_reason=True,
    )
