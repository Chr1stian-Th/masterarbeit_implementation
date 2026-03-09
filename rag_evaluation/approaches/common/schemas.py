"""
Standardized data schemas for RAG approach inputs and outputs.

These dataclasses define the contract between RAG approaches and the
evaluation framework. All approaches must produce output conforming
to :class:`ApproachOutput` so that the evaluator can process them
uniformly.

Example:
    >>> from approaches.common.schemas import QuestionInput, QuestionResult, TokenUsage
    >>> question = QuestionInput(id="q001", question="What is GDPR?", ground_truth="...")
    >>> usage = TokenUsage(prompt_tokens=100, completion_tokens=50)
    >>> result = QuestionResult(
    ...     question_id=question.id,
    ...     input=question.question,
    ...     retriever_context=["Article 1..."],
    ...     output="The GDPR is...",
    ...     ground_truth=question.ground_truth,
    ...     token_usage=usage,
    ...     latency_seconds=1.2
    ... )
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class QuestionInput:
    """A single question from the evaluation corpus.

    Attributes:
        id: Unique identifier for the question (e.g., ``"q001"``).
        question: The natural-language question text.
        ground_truth: The reference answer for evaluation metrics.
    """

    id: str
    question: str
    ground_truth: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QuestionInput":
        """Create a QuestionInput from a dictionary.

        Args:
            data: Dictionary with keys ``id``, ``question``, ``ground_truth``.

        Returns:
            A new :class:`QuestionInput` instance.
        """
        return cls(
            id=data["id"],
            question=data["question"],
            ground_truth=data.get("ground_truth", ""),
        )

    @classmethod
    def load_corpus(cls, path: str) -> list["QuestionInput"]:
        """Load a question corpus from a JSON file.

        Args:
            path: Path to a JSON file containing a list of question objects.

        Returns:
            List of :class:`QuestionInput` instances.
        """
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [cls.from_dict(item) for item in data]


@dataclass
class TokenUsage:
    """Token usage counters for a single question or aggregated totals.

    Attributes:
        prompt_tokens: Tokens consumed by the prompt/input.
        completion_tokens: Tokens consumed by the model's completion/output.
        total_tokens: Sum of prompt + completion tokens.
        embedding_tokens: Tokens consumed by embedding calls (if tracked).
    """

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    embedding_tokens: int = 0

    def __add__(self, other: "TokenUsage") -> "TokenUsage":
        """Sum two TokenUsage instances element-wise.

        Args:
            other: Another :class:`TokenUsage` to add.

        Returns:
            A new :class:`TokenUsage` with summed counters.
        """
        return TokenUsage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
            embedding_tokens=self.embedding_tokens + other.embedding_tokens,
        )

    def to_dict(self) -> dict[str, int]:
        """Serialize to a plain dictionary."""
        return asdict(self)


@dataclass
class QuestionResult:
    """The result of processing a single question through a RAG approach.

    Attributes:
        question_id: Matches :attr:`QuestionInput.id`.
        input: The original question text.
        retriever_context: List of text passages retrieved for this question.
        output: The generated answer.
        ground_truth: The reference answer (carried through for evaluation).
        token_usage: Token consumption for this question.
        latency_seconds: Wall-clock time to process this question.
        metadata: Approach-specific metadata (e.g., classifier tier, relevance scores).
    """

    question_id: str
    input: str
    retriever_context: list[str]
    output: str
    ground_truth: str
    token_usage: TokenUsage
    latency_seconds: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary for JSON output."""
        d = asdict(self)
        d["token_usage"] = self.token_usage.to_dict()
        return d


@dataclass
class ApproachOutput:
    """Complete output from a single RAG approach run.

    This is the top-level structure written to ``outputs/<approach>.json``
    and consumed by the evaluation framework.

    Attributes:
        approach: Name of the RAG approach (e.g., ``"lightrag"``).
        timestamp: ISO-format timestamp of when the run started.
        model_config: Dictionary of model names/settings used.
        results: List of per-question results.
        total_token_usage: Aggregated token usage across all questions.
    """

    approach: str
    timestamp: str
    model_config: dict[str, str]
    results: list[QuestionResult]
    total_token_usage: TokenUsage

    def to_dict(self) -> dict[str, Any]:
        """Serialize the entire output to a JSON-compatible dictionary."""
        return {
            "approach": self.approach,
            "timestamp": self.timestamp,
            "model_config": self.model_config,
            "results": [r.to_dict() for r in self.results],
            "total_token_usage": self.total_token_usage.to_dict(),
        }
