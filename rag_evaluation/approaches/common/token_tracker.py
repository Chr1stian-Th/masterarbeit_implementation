"""
Token usage tracking for OpenAI API calls.

Provides a thin wrapper around the OpenAI client that automatically
records token consumption for both chat completions and embedding
calls. This enables accurate cost tracking and comparison across
RAG approaches.

Usage:
    >>> from approaches.common.token_tracker import TrackedOpenAIClient
    >>> client = TrackedOpenAIClient(api_key="sk-...")
    >>> response, usage = client.chat_completion(
    ...     model="gpt-4o-mini",
    ...     messages=[{"role": "user", "content": "Hello"}],
    ...     temperature=0.1
    ... )
    >>> print(f"Used {usage.total_tokens} tokens")
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field

from openai import OpenAI

from approaches.common.schemas import TokenUsage


@dataclass
class TrackedOpenAIClient:
    """OpenAI client wrapper that tracks token usage across all calls.

    Thread-safe: uses a lock to protect cumulative usage counters,
    making it safe for use with ``concurrent.futures.ThreadPoolExecutor``.

    Attributes:
        api_key: OpenAI API key.
        base_url: Optional custom base URL (for OpenAI-compatible APIs).
        cumulative_usage: Running total of all token usage.
    """

    api_key: str
    base_url: str | None = None
    cumulative_usage: TokenUsage = field(default_factory=TokenUsage)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _client: OpenAI = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialize the underlying OpenAI client."""
        kwargs = {"api_key": self.api_key}
        if self.base_url:
            kwargs["base_url"] = self.base_url
        self._client = OpenAI(**kwargs)

    def chat_completion(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int | None = None,
        **kwargs,
    ) -> tuple[str, TokenUsage]:
        """Send a chat completion request and track token usage.

        Args:
            model: Model identifier (e.g., ``"gpt-4o-mini"``).
            messages: List of message dicts with ``role`` and ``content``.
            temperature: Sampling temperature (0.0 = deterministic).
            max_tokens: Maximum tokens in the response.
            **kwargs: Additional arguments passed to the OpenAI API.

        Returns:
            A tuple of ``(response_text, token_usage)`` where
            ``response_text`` is the assistant's message content and
            ``token_usage`` captures the tokens consumed by this call.
        """
        call_kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            **kwargs,
        }
        if max_tokens is not None:
            call_kwargs["max_tokens"] = max_tokens

        response = self._client.chat.completions.create(**call_kwargs)

        # Extract usage from the response
        usage = TokenUsage(
            prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
            completion_tokens=response.usage.completion_tokens if response.usage else 0,
            total_tokens=response.usage.total_tokens if response.usage else 0,
        )

        # Thread-safe accumulation
        with self._lock:
            self.cumulative_usage = self.cumulative_usage + usage

        content = response.choices[0].message.content or ""
        return content, usage

    def embed(
        self,
        model: str,
        texts: list[str],
    ) -> tuple[list[list[float]], TokenUsage]:
        """Generate embeddings and track token usage.

        Args:
            model: Embedding model identifier (e.g., ``"text-embedding-3-small"``).
            texts: List of text strings to embed.

        Returns:
            A tuple of ``(embeddings, token_usage)`` where ``embeddings``
            is a list of float vectors and ``token_usage`` captures
            the tokens consumed.
        """
        response = self._client.embeddings.create(
            model=model,
            input=texts,
        )

        usage = TokenUsage(
            embedding_tokens=response.usage.total_tokens if response.usage else 0,
        )

        with self._lock:
            self.cumulative_usage = self.cumulative_usage + usage

        embeddings = [item.embedding for item in response.data]
        return embeddings, usage

    def get_cumulative_usage(self) -> TokenUsage:
        """Return a snapshot of the cumulative token usage.

        Returns:
            A copy of the current cumulative :class:`TokenUsage`.
        """
        with self._lock:
            return TokenUsage(
                prompt_tokens=self.cumulative_usage.prompt_tokens,
                completion_tokens=self.cumulative_usage.completion_tokens,
                total_tokens=self.cumulative_usage.total_tokens,
                embedding_tokens=self.cumulative_usage.embedding_tokens,
            )

    def reset_cumulative_usage(self) -> None:
        """Reset cumulative usage counters to zero."""
        with self._lock:
            self.cumulative_usage = TokenUsage()
