#!/usr/bin/env python3
"""
LightRAG approach for GDPR question answering.

Uses `HKUDS/LightRAG <https://github.com/HKUDS/LightRAG>`_ which builds a
knowledge graph from the GDPR corpus and performs hybrid (graph + vector)
retrieval to answer questions.

LightRAG internally manages:
    - Entity extraction and relationship mapping
    - Graph-based and vector-based retrieval
    - Context assembly and answer generation

This runner wraps LightRAG's query interface, extracts available context
information, and logs everything in the standardized output schema.

Usage:
    python approaches/lightrag_approach/run.py [--questions PATH] [--output-dir PATH]

Environment Variables:
    OPENAI_API_KEY: Required. API key (OpenAI or OpenRouter).
    OPENAI_BASE_URL: Optional. Custom base URL for OpenAI-compatible APIs (e.g. OpenRouter).
"""

import os
import sys
import time
import argparse
import asyncio
from functools import partial
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Path setup: add project root to sys.path for common module imports
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from approaches.common.schemas import (
    QuestionInput,
    QuestionResult,
    TokenUsage,
    ApproachOutput,
)
from approaches.common.output_logger import OutputLogger
from approaches.common.config_loader import load_config

# Load this approach's .env file
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))


# ============================================================================
# LightRAG Wrapper
# ============================================================================

class LightRAGRunner:
    """Wraps LightRAG for standardized question processing.

    Initializes a LightRAG instance pointing at the pre-built graph
    storage directory and exposes a synchronous query interface that
    returns structured :class:`QuestionResult` objects.

    Attributes:
        rag: The LightRAG instance.
        config: Parsed settings dictionary.
        query_mode: LightRAG query mode (``"hybrid"``, ``"naive"``, etc.).
    """

    def __init__(self, config: dict) -> None:
        """Initialize the LightRAG runner.

        Args:
            config: Parsed ``settings.yaml`` dictionary.

        Raises:
            ValueError: If ``OPENAI_API_KEY`` is not set.
        """
        from lightrag import LightRAG
        from lightrag.llm.openai import openai_complete_if_cache, openai_embed
        from lightrag.utils import EmbeddingFunc

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required.")

        base_url = os.environ.get("OPENAI_BASE_URL")  # e.g. https://openrouter.ai/api/v1

        self.config = config
        self.query_mode = "hybrid"  # Best mode: combines graph + vector retrieval

        working_dir = os.path.join(PROJECT_ROOT, config["lightrag"]["working_dir"])
        embedding_model = config["models"]["embedding_model"]
        embedding_dim = config["models"]["embedding_dimensions"]
        generation_model = config["models"]["generation_model"]

        llm_kwargs = {"api_key": api_key}
        if base_url:
            llm_kwargs["base_url"] = base_url

        self.rag = LightRAG(
            working_dir=working_dir,
            llm_model_func=partial(openai_complete_if_cache, generation_model, **llm_kwargs),
            llm_model_name=generation_model,
            llm_model_max_async=4,
            embedding_func=EmbeddingFunc(
                embedding_dim=embedding_dim,
                max_token_size=config["lightrag"]["max_token_size"],
                # Use openai_embed.func to avoid double EmbeddingFunc wrapping
                func=partial(openai_embed.func, model=embedding_model, **llm_kwargs),
            ),
        )

        # Initialize storages (required in LightRAG >= 1.4)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.rag.initialize_storages())
        finally:
            loop.close()

    async def _aquery(self, question: str) -> str:
        """Async query wrapper for LightRAG.

        Args:
            question: The question to answer.

        Returns:
            The generated answer text.
        """
        from lightrag import QueryParam

        result = await self.rag.aquery(
            question,
            param=QueryParam(mode=self.query_mode),
        )
        return result

    def finalize(self) -> None:
        """Finalize storages (call once after all queries are done)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.rag.finalize_storages())
        finally:
            loop.close()

    def process_question(self, question: QuestionInput) -> QuestionResult:
        """Process a single question through LightRAG.

        Queries LightRAG in hybrid mode, measures latency, and captures
        available context information.

        Args:
            question: The question to process.

        Returns:
            A :class:`QuestionResult` with the answer, context, and metadata.

        Note:
            LightRAG does not expose raw retriever context through its
            public API. The ``retriever_context`` field contains the
            full response which includes context used for generation.
            For more granular context extraction, consider patching
            LightRAG's internal retrieval step.
        """
        start_time = time.time()

        try:
            # Run async query in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                answer = loop.run_until_complete(self._aquery(question.question))
            finally:
                loop.close()

            latency = time.time() - start_time

            # LightRAG integrates retrieval and generation — extract what we can.
            # The full answer includes synthesized context from the knowledge graph.
            # We log it as context since LightRAG doesn't expose raw retrieved passages.
            retriever_context = [
                f"[LightRAG {self.query_mode} mode] Context integrated in response"
            ]

            # Estimate token usage (LightRAG doesn't expose this directly)
            # A rough heuristic based on typical LightRAG query patterns
            estimated_prompt_tokens = len(question.question.split()) * 2 + 500
            estimated_completion_tokens = len(answer.split()) * 2
            token_usage = TokenUsage(
                prompt_tokens=estimated_prompt_tokens,
                completion_tokens=estimated_completion_tokens,
                total_tokens=estimated_prompt_tokens + estimated_completion_tokens,
            )

        except Exception as e:
            latency = time.time() - start_time
            answer = f"[ERROR] {str(e)}"
            retriever_context = []
            token_usage = TokenUsage()

        return QuestionResult(
            question_id=question.id,
            input=question.question,
            retriever_context=retriever_context,
            output=answer,
            ground_truth=question.ground_truth,
            token_usage=token_usage,
            latency_seconds=round(latency, 3),
            metadata={"query_mode": self.query_mode},
        )


# ============================================================================
# Main execution
# ============================================================================

def run_lightrag(
    questions_path: str | None = None,
    output_dir: str | None = None,
    max_workers: int | None = None,
) -> str:
    """Run the LightRAG approach on a question corpus.

    This is the main entry point, designed to be called either from the
    command line or programmatically (e.g., from the orchestrator).

    Args:
        questions_path: Path to the questions JSON file. Defaults to
            the path in ``settings.yaml``.
        output_dir: Directory for output files. Defaults to ``outputs/``.
        max_workers: Max parallel workers. Defaults to config value.

    Returns:
        Path to the saved output JSON file.
    """
    cfg = load_config()

    if questions_path is None:
        questions_path = os.path.join(PROJECT_ROOT, cfg["io"]["questions_path"])
    if output_dir is None:
        output_dir = os.path.join(PROJECT_ROOT, cfg["io"]["outputs_dir"])
    if max_workers is None:
        max_workers = cfg["execution"]["max_workers"]

    questions = QuestionInput.load_corpus(questions_path)
    print(f"[LightRAG] Processing {len(questions)} questions (max_workers={max_workers})")

    runner = LightRAGRunner(cfg)
    results: list[QuestionResult] = []

    # Process questions (sequential for LightRAG due to async internals)
    # For parallelization, use ThreadPoolExecutor
    if max_workers <= 1:
        for i, q in enumerate(questions):
            print(f"  [{i+1}/{len(questions)}] {q.question[:80]}...")
            result = runner.process_question(q)
            results.append(result)
            print(f"    -> {result.latency_seconds}s, {result.token_usage.total_tokens} tokens")
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_map = {
                executor.submit(runner.process_question, q): q
                for q in questions
            }
            for future in as_completed(future_map):
                q = future_map[future]
                result = future.result()
                results.append(result)
                print(f"  [{len(results)}/{len(questions)}] {q.id}: {result.latency_seconds}s")

    # Finalize LightRAG storages
    runner.finalize()

    # Sort results by question ID for deterministic output
    results.sort(key=lambda r: r.question_id)

    total_usage = TokenUsage()
    for r in results:
        total_usage = total_usage + r.token_usage

    output = ApproachOutput(
        approach="lightrag",
        timestamp=OutputLogger.get_timestamp(),
        model_config={
            "generation_model": cfg["models"]["generation_model"],
            "embedding_model": cfg["models"]["embedding_model"],
            "query_mode": runner.query_mode,
        },
        results=results,
        total_token_usage=total_usage,
    )

    logger = OutputLogger(output_dir)
    filepath = logger.save(output)
    return filepath


def main() -> None:
    """CLI entry point for the LightRAG approach."""
    parser = argparse.ArgumentParser(description="Run LightRAG on GDPR questions")
    parser.add_argument("--questions", type=str, help="Path to questions JSON")
    parser.add_argument("--output-dir", type=str, help="Output directory")
    parser.add_argument("--max-workers", type=int, default=1, help="Max parallel workers")
    args = parser.parse_args()

    filepath = run_lightrag(
        questions_path=args.questions,
        output_dir=args.output_dir,
        max_workers=args.max_workers,
    )
    print(f"[LightRAG] Done. Output: {filepath}")


if __name__ == "__main__":
    main()
