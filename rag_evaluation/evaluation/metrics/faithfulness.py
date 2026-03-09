"""
Faithfulness metric implementation using DeepEval.

Faithfulness measures whether the generated answer is factually consistent
with the retrieved context passages. An answer is faithful if every claim
it makes can be traced back to information in the retriever context.

This is a critical metric for RAG systems because it directly measures
the degree to which the model hallucinates vs. stays grounded in the
retrieved evidence.

DeepEval's ``FaithfulnessMetric`` uses an LLM-as-judge approach:

1. Extract claims from the generated answer.
2. For each claim, verify whether it is supported by the retrieval context.
3. Compute the faithfulness score as the ratio of supported claims.

Adding this metric:
    This module is automatically discovered by the metrics registry.
    No additional registration is needed.

See Also:
    - `DeepEval Faithfulness Docs <https://docs.confident-ai.com/docs/metrics-faithfulness>`_
"""

from __future__ import annotations

from typing import Any

from deepeval.metrics import FaithfulnessMetric
from deepeval.models import DeepEvalBaseLLM


# Metric identifier used by the registry
METRIC_NAME = "faithfulness"


class OpenAIModel(DeepEvalBaseLLM):
    """Wrapper to configure DeepEval with a specific OpenAI model.

    DeepEval can auto-detect OpenAI models, but this wrapper gives
    explicit control over which model is used for evaluation.

    Attributes:
        model_name: The OpenAI model identifier.
    """

    def __init__(self, model_name: str = "gpt-4o-mini") -> None:
        """Initialize with a specific model name.

        Args:
            model_name: OpenAI model to use for evaluation judgments.
        """
        self.model_name = model_name

    def load_model(self) -> str:
        """Return the model identifier (no-op for OpenAI API models).

        Returns:
            The model name string.
        """
        return self.model_name

    def generate(self, prompt: str) -> str:
        """Generate a response using the OpenAI API.

        Args:
            prompt: The prompt to send to the model.

        Returns:
            The model's response text.
        """
        from openai import OpenAI

        client = OpenAI()
        response = client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        return response.choices[0].message.content or ""

    async def a_generate(self, prompt: str) -> str:
        """Async version of generate.

        Args:
            prompt: The prompt to send to the model.

        Returns:
            The model's response text.
        """
        # DeepEval may call this for async evaluation
        return self.generate(prompt)

    def get_model_name(self) -> str:
        """Return the model name for DeepEval logging.

        Returns:
            The model name string.
        """
        return self.model_name


def create_metric(
    model: str = "gpt-4o-mini",
    threshold: float = 0.7,
    **kwargs: Any,
) -> FaithfulnessMetric:
    """Factory function to create a configured FaithfulnessMetric.

    This is called by the metrics registry when instantiating metrics.

    Args:
        model: OpenAI model for LLM-as-judge evaluation.
        threshold: Minimum score (0-1) to consider a test case as passing.
            Defaults to 0.7 (70% of claims must be supported).
        **kwargs: Additional keyword arguments (unused, for registry compat).

    Returns:
        A configured :class:`FaithfulnessMetric` instance.
    """
    return FaithfulnessMetric(
        threshold=threshold,
        model=model,
        include_reason=True,
    )
