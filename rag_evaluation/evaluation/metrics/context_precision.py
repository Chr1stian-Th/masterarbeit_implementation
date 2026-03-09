"""
Context Precision metric implementation using DeepEval.

Context Precision measures how relevant the retrieved context passages are
to the question being asked. It answers: "Of all the chunks retrieved, how
many were actually useful for generating the answer?"

A low context precision score means the retriever is returning noisy or
irrelevant documents alongside useful ones, which can confuse the generator
and waste context window space.

DeepEval's ``ContextualPrecisionMetric`` uses an LLM-as-judge approach:

1. For each retrieved context chunk, determine whether it was relevant to
   the question and expected output.
2. Compute precision as a weighted positional average (higher-ranked
   relevant chunks score better than lower-ranked ones).

Adding this metric:
    This module is automatically discovered by the metrics registry.
    No additional registration is needed.

See Also:
    - `DeepEval Contextual Precision Docs <https://docs.confident-ai.com/docs/metrics-contextual-precision>`_
"""

from __future__ import annotations

from typing import Any

from deepeval.metrics import ContextualPrecisionMetric


# Metric identifier used by the registry
METRIC_NAME = "context_precision"


def create_metric(
    model: str = "gpt-4o-mini",
    threshold: float = 0.7,
    **kwargs: Any,
) -> ContextualPrecisionMetric:
    """Factory function to create a configured ContextualPrecisionMetric.

    This is called by the metrics registry when instantiating metrics.

    Args:
        model: OpenAI model for LLM-as-judge evaluation.
        threshold: Minimum score (0-1) to consider a test case as passing.
            Defaults to 0.7 (70% of retrieved chunks should be relevant).
        **kwargs: Additional keyword arguments (unused, for registry compat).

    Returns:
        A configured :class:`ContextualPrecisionMetric` instance.
    """
    return ContextualPrecisionMetric(
        threshold=threshold,
        model=model,
        include_reason=True,
    )
