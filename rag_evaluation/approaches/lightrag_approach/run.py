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
    storage directory and exposes an async query interface that
    returns structured :class:`QuestionResult` objects.

    All async operations (initialize, query, finalize) must be awaited
    within the same event loop — use :func:`_run_all` as the single
    ``asyncio.run()`` entry point.

    Attributes:
        rag: The LightRAG instance.
        config: Parsed settings dictionary.
        query_mode: LightRAG query mode (``"hybrid"``, ``"naive"``, etc.).
    """

    def __init__(self, config: dict) -> None:
        """Set up the LightRAG instance (no async operations here).

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

    async def initialize(self) -> None:
        """Initialize storages (required in LightRAG >= 1.4)."""
        await self.rag.initialize_storages()

    async def finalize(self) -> None:
        """Finalize storages (call once after all queries are done)."""
        await self.rag.finalize_storages()

    @staticmethod
    def _parse_context_sections(raw_context: str) -> list[str]:
        """Parse LightRAG's formatted context string into individual passages.

        LightRAG returns context as a single string containing CSV-formatted
        sections for entities, relationships, and document chunks. This method
        splits the context into individual passages suitable for LLM-as-a-judge
        evaluation, comparable to the chunk-level passages logged by other
        approaches (e.g. CRAG).

        Only the ``Document Chunks`` section is extracted, as it contains the
        actual retrieved text passages. Entity and relationship summaries from
        the knowledge graph are logged separately in metadata.

        Args:
            raw_context: The formatted context string from LightRAG's
                ``only_need_context=True`` query.

        Returns:
            A list of passage strings (document chunks). Falls back to the
            full raw context as a single-element list if parsing fails.
        """
        if not raw_context or not raw_context.strip():
            return []

        chunks: list[str] = []
        kg_data: list[str] = []

        # LightRAG context has sections like "-----Entities-----",
        # "-----Relationships-----", "-----Document Chunks-----"
        # Split on section headers to isolate the document chunks.
        sections = raw_context.split("-----")
        current_section = None

        for part in sections:
            stripped = part.strip()
            if not stripped:
                continue

            header = stripped.lower()
            if "document chunks" in header or "sources" in header or "text units" in header:
                current_section = "chunks"
                continue
            elif "entit" in header:
                current_section = "entities"
                continue
            elif "relat" in header:
                current_section = "relationships"
                continue

            if current_section == "chunks":
                # Each chunk is typically separated by a delimiter or newlines.
                # Split on common chunk separators used by LightRAG.
                for chunk in stripped.split("\n\n"):
                    chunk = chunk.strip()
                    if chunk and len(chunk) > 20:  # skip tiny fragments
                        chunks.append(chunk)
            elif current_section in ("entities", "relationships"):
                if stripped and len(stripped) > 10:
                    kg_data.append(stripped)

        # If no structured sections found, treat the whole context as passages
        if not chunks and not kg_data:
            # Fall back: split on double newlines as a best-effort parse
            for passage in raw_context.split("\n\n"):
                passage = passage.strip()
                if passage and len(passage) > 20:
                    chunks.append(passage)

        return chunks

    async def process_question(self, question: QuestionInput) -> QuestionResult:
        """Process a single question through LightRAG.

        Performs two queries per question in a specific order to ensure
        that the logged context matches what the LLM actually used:

        1. A ``only_need_context=True`` query that runs the full retrieval
           pipeline (keyword extraction → vector search → graph traversal →
           context assembly) but returns early **before** calling the LLM.
           This populates LightRAG's internal ``llm_response_cache`` with the
           keyword extraction result for this query.
        2. A normal query to get the generated answer. Because the keyword
           extraction LLM call from step 1 is cached, the second call reuses
           the **same keywords**, which means it queries the same vectors and
           traverses the same graph paths, producing identical retrieval
           results. The only non-determinism (LLM keyword extraction) is
           thus eliminated.

        The context from step 1 is logged in ``retriever_context`` for
        downstream LLM-as-a-judge evaluation.

        Args:
            question: The question to process.

        Returns:
            A :class:`QuestionResult` with the answer, retrieved context,
            and metadata.
        """
        from lightrag import QueryParam

        start_time = time.time()

        try:
            # --- Step 1: Retrieve the raw context (no LLM generation) ---
            # Uses only_need_context=True which runs the full retrieval
            # pipeline inside kg_query() but returns the assembled context
            # string *before* calling the LLM for answer generation.
            # Crucially, this also caches the keyword extraction result,
            # so the subsequent normal query will reuse the same keywords.
            raw_context = await self.rag.aquery(
                question.question,
                param=QueryParam(
                    mode=self.query_mode,
                    enable_rerank=False,
                    only_need_context=True,
                ),
            )

            # --- Step 2: Generate the answer (normal query) ---
            # The keyword extraction LLM call is now cached from step 1,
            # so this query will retrieve the same context and pass it to
            # the LLM for answer generation.
            answer = await self.rag.aquery(
                question.question,
                param=QueryParam(mode=self.query_mode, enable_rerank=False),
            )

            latency = time.time() - start_time

            # Handle QueryContextResult dataclass (LightRAG >= 1.4.x)
            # or plain string (older versions).
            if hasattr(raw_context, "content"):
                context_str = raw_context.content or ""
            elif isinstance(raw_context, str):
                context_str = raw_context
            else:
                context_str = str(raw_context)

            # Similarly handle answer if it's a result object
            if hasattr(answer, "content"):
                answer_str = answer.content or ""
            elif isinstance(answer, str):
                answer_str = answer
            else:
                answer_str = str(answer)

            # Parse context into individual passages for fair comparison
            # with other approaches (e.g. CRAG) that log per-chunk passages.
            retriever_context = self._parse_context_sections(context_str)

            # Estimate token usage (LightRAG doesn't expose this directly)
            # Approximation based on the actual retrieved context size
            context_tokens = len(context_str.split()) if context_str else 0
            estimated_prompt_tokens = context_tokens + len(question.question.split()) + 200
            estimated_completion_tokens = len(answer_str.split()) * 2
            token_usage = TokenUsage(
                prompt_tokens=estimated_prompt_tokens,
                completion_tokens=estimated_completion_tokens,
                total_tokens=estimated_prompt_tokens + estimated_completion_tokens,
            )

        except Exception as e:
            latency = time.time() - start_time
            answer_str = f"[ERROR] {str(e)}"
            retriever_context = []
            token_usage = TokenUsage()

        return QuestionResult(
            question_id=question.id,
            input=question.question,
            retriever_context=retriever_context,
            output=answer_str,
            ground_truth=question.ground_truth,
            token_usage=token_usage,
            latency_seconds=round(latency, 3),
            metadata={"query_mode": self.query_mode},
        )


# ============================================================================
# Main execution
# ============================================================================

async def _run_all(
    cfg: dict,
    questions: list[QuestionInput],
    max_workers: int,
) -> tuple["LightRAGRunner", list[QuestionResult]]:
    """Run init → all queries → finalize inside a single event loop.

    Args:
        cfg: Parsed settings dictionary.
        questions: List of questions to process.
        max_workers: Max concurrent queries (uses asyncio.Semaphore).

    Returns:
        Tuple of (runner, results).
    """
    runner = LightRAGRunner(cfg)
    await runner.initialize()

    results: list[QuestionResult] = []

    if max_workers <= 1:
        for i, q in enumerate(questions):
            print(f"  [{i+1}/{len(questions)}] {q.question[:80]}...")
            result = await runner.process_question(q)
            results.append(result)
            print(f"    -> {result.latency_seconds}s, {result.token_usage.total_tokens} tokens")
    else:
        sem = asyncio.Semaphore(max_workers)
        completed = 0

        async def bounded(i: int, q: QuestionInput) -> QuestionResult:
            nonlocal completed
            async with sem:
                print(f"  [{i+1}/{len(questions)}] {q.question[:80]}...")
                result = await runner.process_question(q)
                completed += 1
                print(f"    [{completed}/{len(questions)}] {q.id}: {result.latency_seconds}s")
                return result

        results = list(
            await asyncio.gather(*[bounded(i, q) for i, q in enumerate(questions)])
        )

    await runner.finalize()
    return runner, results


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

    runner, results = asyncio.run(_run_all(cfg, questions, max_workers))

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