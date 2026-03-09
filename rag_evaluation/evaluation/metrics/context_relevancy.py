"""
Context Relevancy metric implementation using DeepEval.

Context Relevancy measures how focused the retrieved context is on the
input question — specifically, what proportion of the retrieved content
is directly relevant to answering it.

The distinction from context precision is subtle but important:

- **Context Precision** evaluates whether each retrieved *chunk* as a
  whole is relevant (chunk-level binary judgement, positionally weighted).
- **Context Relevancy** evaluates what fraction of the *sentences or
  statements* inside the retrieved context are relevant to the question
  (finer-grained, content-level).

A retriever that returns mostly relevant chunks but with each chunk
containing many off-topic sentences will score well on precision but
poorly on relevancy.

DeepEval's ``ContextualRelevancyMetric`` uses an LLM-as-judge approach:

1. Extract individual sentences/statements from all retrieved chunks.
2. For each statement, determine whether it is relevant to the question.
3. Compute relevancy as the ratio of relevant statements.

Adding this metric:
    This module is automatically discovered by the metrics registry.
    No additional registration is needed.

See Also:
    - `DeepEval Contextual Relevancy Docs <https://docs.confident-ai.com/docs/metrics-contextual-relevancy>`_
"""

from __future__ import annotations

from typing import Any

from deepeval.metrics import ContextualRelevancyMetric


# Metric identifier used by the registry
METRIC_NAME = "context_relevancy"


def create_metric(
    model: str = "gpt-4o-mini",
    threshold: float = 0.7,
    **kwargs: Any,
) -> ContextualRelevancyMetric:
    """Factory function to create a configured ContextualRelevancyMetric.

    This is called by the metrics registry when instantiating metrics.

    Args:
        model: OpenAI model for LLM-as-judge evaluation.
        threshold: Minimum score (0-1) to consider a test case as passing.
            Defaults to 0.7 (70% of retrieved statements must be relevant
            to the question).
        **kwargs: Additional keyword arguments (unused, for registry compat).

    Returns:
        A configured :class:`ContextualRelevancyMetric` instance.
    """
    return ContextualRelevancyMetric(
        threshold=threshold,
        model=model,
        include_reason=True,
    )
