"""
Context Recall metric implementation using DeepEval.

Context Recall measures whether the retrieved context contains all the
information needed to produce the expected (ground truth) answer. It
answers: "Did the retriever find everything it needed to find?"

While context precision asks whether retrieved chunks are noise-free,
context recall asks whether the retriever missed any relevant chunks.
Together they give a full picture of retrieval quality.

DeepEval's ``ContextualRecallMetric`` uses an LLM-as-judge approach:

1. Break the expected output (ground truth) into individual statements.
2. For each statement, check whether it is attributable to at least one
   retrieved context chunk.
3. Compute recall as the ratio of ground-truth statements covered by the
   retrieval context.

Note:
    This metric requires ``expected_output`` to be set on the test case
    (i.e. ground-truth answers must be present in the evaluation data).

Adding this metric:
    This module is automatically discovered by the metrics registry.
    No additional registration is needed.

See Also:
    - `DeepEval Contextual Recall Docs <https://docs.confident-ai.com/docs/metrics-contextual-recall>`_
"""

from __future__ import annotations

from typing import Any

from deepeval.metrics import ContextualRecallMetric


# Metric identifier used by the registry
METRIC_NAME = "context_recall"


def create_metric(
    model: str = "gpt-4o-mini",
    threshold: float = 0.7,
    **kwargs: Any,
) -> ContextualRecallMetric:
    """Factory function to create a configured ContextualRecallMetric.

    This is called by the metrics registry when instantiating metrics.

    Args:
        model: OpenAI model for LLM-as-judge evaluation.
        threshold: Minimum score (0-1) to consider a test case as passing.
            Defaults to 0.7 (70% of ground-truth statements must be
            attributable to the retrieved context).
        **kwargs: Additional keyword arguments (unused, for registry compat).

    Returns:
        A configured :class:`ContextualRecallMetric` instance.
    """
    return ContextualRecallMetric(
        threshold=threshold,
        model=model,
        include_reason=True,
    )
