#!/usr/bin/env python3
"""
Agentic RAG approach for GDPR question answering.

Implements an adaptive retrieval pipeline with three key stages:

1. Query Classifier:
   An LLM-based classifier that categorizes each question into one of
   three complexity tiers:

   - ``no_retrieval``: Answerable from parametric knowledge alone.
   - ``single_step``: Needs one targeted lookup from the GDPR corpus.
   - ``multi_step``: Requires reasoning across multiple articles/concepts.

2. Dynamic Retrieval Execution:
   The retrieval strategy adapts based on the classifier output:

   - *No retrieval*: Direct LLM generation without context.
   - *Single-step*: Standard dense retrieval from ChromaDB.
   - *Multi-step*: Iterative retrieval where intermediate passages inform
     follow-up sub-queries (orchestrator-worker pattern).

3. Hallucination Check:
   After generation, the LLM evaluates whether its answer is actually
   supported by the retrieved passages. If not, it triggers re-retrieval
   with a refined query and regenerates.

Usage:
    python approaches/agentic_rag/run.py [--questions PATH] [--output-dir PATH]

Environment Variables:
    OPENAI_API_KEY: Required. Your OpenAI API key.
"""

import os
import sys
import json
import time
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from approaches.common.schemas import (
    QuestionInput,
    QuestionResult,
    TokenUsage,
    ApproachOutput,
)
from approaches.common.token_tracker import TrackedOpenAIClient
from approaches.common.output_logger import OutputLogger
from approaches.common.config_loader import load_config

# Load this approach's .env file
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

import chromadb
from chromadb.config import Settings


# ============================================================================
# Prompt Templates
# ============================================================================

CLASSIFIER_PROMPT = """You are a GDPR question complexity classifier. Analyze the following question and classify it into exactly one of these three tiers:

1. **no_retrieval** — The question is answerable from general knowledge about GDPR without needing to look up specific articles or provisions. Examples: "What year did GDPR come into force?", "What does GDPR stand for?", "Which body oversees GDPR enforcement?"

2. **single_step** — The question requires looking up one specific article, provision, or concept from the GDPR text. Examples: "What does Article 17 say about the right to erasure?", "What are the lawful bases for processing under Article 6?", "What is the maximum fine under GDPR?"

3. **multi_step** — The question requires reasoning across multiple GDPR articles, comparing provisions, or synthesizing information from different parts of the regulation. Examples: "Under what conditions can a legitimate interest override a data subject's objection?", "How do Articles 6, 9, and 22 interact for automated decision-making about health data?", "Compare the rights under Articles 15-22 and their exceptions."

Respond with ONLY the tier name: no_retrieval, single_step, or multi_step

Question: {question}

Classification:"""

GENERATION_PROMPT = """You are a GDPR legal expert. Answer the following question based on the provided context from the GDPR regulation.

Context:
{context}

Question: {question}

Provide a clear, accurate, and comprehensive answer based strictly on the provided context. If the context does not contain sufficient information, state what is available and what is missing.

Answer:"""

GENERATION_NO_CONTEXT_PROMPT = """You are a GDPR legal expert. Answer the following question based on your knowledge of the General Data Protection Regulation (GDPR).

Question: {question}

Provide a clear, accurate answer.

Answer:"""

HALLUCINATION_CHECK_PROMPT = """You are a grounding evaluator. Your task is to determine whether the given answer is fully supported by the provided context passages.

Context passages:
{context}

Question: {question}

Answer to evaluate:
{answer}

Evaluate whether EVERY claim in the answer is supported by the context passages. Respond with a JSON object:
{{
    "is_grounded": true/false,
    "confidence": 0.0-1.0,
    "unsupported_claims": ["list of claims not found in context"],
    "suggested_refinement": "if not grounded, suggest a refined search query"
}}

Evaluation:"""

SUBQUERY_DECOMPOSITION_PROMPT = """You are a GDPR research assistant. The following question requires information from multiple parts of the GDPR regulation.

Original question: {question}

Already retrieved context:
{context}

Based on what has been retrieved so far, identify what sub-concepts or GDPR provisions are still needed to fully answer the question. Generate 1-3 focused sub-queries to retrieve the missing information.

Respond with a JSON array of sub-query strings:
["sub-query 1", "sub-query 2"]

Sub-queries:"""


# ============================================================================
# ChromaDB Retriever
# ============================================================================

class ChromaRetriever:
    """Dense retriever backed by a persistent ChromaDB collection.

    Performs similarity search against the pre-indexed GDPR corpus using
    the same embedding model configured globally for fair cross-approach
    comparison.

    Attributes:
        collection: The ChromaDB collection to search.
        client: Tracked OpenAI client for embedding generation.
        embedding_model: Name of the embedding model.
        top_k: Number of documents to retrieve per query.
    """

    def __init__(
        self,
        tracked_client: TrackedOpenAIClient,
        config: dict,
    ) -> None:
        """Initialize the ChromaDB retriever.

        Args:
            tracked_client: OpenAI client wrapper with token tracking.
            config: Parsed settings dictionary.
        """
        persist_dir = os.path.join(PROJECT_ROOT, config["chromadb"]["persist_directory"])
        collection_name = config["chromadb"]["collection_name"]

        chroma_client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = chroma_client.get_collection(name=collection_name)
        self.client = tracked_client
        self.embedding_model = config["models"]["embedding_model"]
        self.top_k = config["retrieval"]["top_k"]
        self.similarity_threshold = config["retrieval"]["similarity_threshold"]

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
    ) -> list[str]:
        """Retrieve relevant passages for a query.

        Embeds the query, searches ChromaDB, and returns documents
        that exceed the similarity threshold.

        Args:
            query: The search query text.
            top_k: Override for the number of results. Defaults to
                the configured ``top_k``.

        Returns:
            List of retrieved passage texts, ordered by relevance.
        """
        k = top_k or self.top_k

        # Generate query embedding
        embeddings, _ = self.client.embed(self.embedding_model, [query])

        results = self.collection.query(
            query_embeddings=embeddings,
            n_results=k,
            include=["documents", "distances"],
        )

        documents = results["documents"][0] if results["documents"] else []
        distances = results["distances"][0] if results["distances"] else []

        # Filter by similarity threshold (ChromaDB returns distances, not similarities)
        # For cosine distance: similarity = 1 - distance
        filtered = []
        for doc, dist in zip(documents, distances):
            similarity = 1.0 - dist
            if similarity >= self.similarity_threshold:
                filtered.append(doc)

        return filtered


# ============================================================================
# Agentic RAG Pipeline
# ============================================================================

class AgenticRAGRunner:
    """Orchestrates the full Agentic RAG pipeline.

    Manages the three-stage process: classify → retrieve → generate → check,
    with each stage using the tracked OpenAI client for consistent token
    accounting.

    Attributes:
        client: Tracked OpenAI client for all LLM calls.
        retriever: ChromaDB retriever for passage lookup.
        config: Parsed settings dictionary.
    """

    def __init__(self, config: dict) -> None:
        """Initialize the Agentic RAG pipeline.

        Args:
            config: Parsed ``settings.yaml`` dictionary.

        Raises:
            ValueError: If ``OPENAI_API_KEY`` is not set.
        """
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required.")

        base_url = os.environ.get("OPENAI_BASE_URL")
        self.client = TrackedOpenAIClient(api_key=api_key, base_url=base_url)
        self.retriever = ChromaRetriever(self.client, config)
        self.config = config

        self.gen_model = config["models"]["generation_model"]
        self.cls_model = config["models"]["classifier_model"]
        self.cls_temp = config["agentic_rag"]["classifier_temperature"]
        self.gen_temp = config["agentic_rag"]["generation_temperature"]
        self.hal_temp = config["agentic_rag"]["hallucination_check_temperature"]
        self.max_hal_retries = config["agentic_rag"]["max_hallucination_retries"]
        self.max_retrieval_iters = config["retrieval"]["max_retrieval_iterations"]

    def classify_query(self, question: str) -> str:
        """Classify a question into a complexity tier.

        Uses the classifier LLM to determine whether the question needs
        no retrieval, single-step retrieval, or multi-step retrieval.

        Args:
            question: The question text.

        Returns:
            One of ``"no_retrieval"``, ``"single_step"``, or ``"multi_step"``.
        """
        prompt = CLASSIFIER_PROMPT.format(question=question)
        response, _ = self.client.chat_completion(
            model=self.cls_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.cls_temp,
            max_tokens=20,
        )

        classification = response.strip().lower().replace('"', "").replace("'", "")

        # Normalize to valid tier
        if "no_retrieval" in classification or "no retrieval" in classification:
            return "no_retrieval"
        elif "multi_step" in classification or "multi step" in classification:
            return "multi_step"
        else:
            return "single_step"

    def retrieve_single_step(self, question: str) -> list[str]:
        """Perform a single dense retrieval against the GDPR corpus.

        Args:
            question: The question to retrieve passages for.

        Returns:
            List of relevant passage texts.
        """
        return self.retriever.retrieve(question)

    def retrieve_multi_step(self, question: str) -> list[str]:
        """Perform iterative multi-step retrieval.

        First retrieves for the initial question, then identifies
        unresolved sub-concepts and issues follow-up retrievals
        to fill gaps. Implements the orchestrator-worker pattern.

        Args:
            question: The original complex question.

        Returns:
            Combined list of all retrieved passages (deduplicated).
        """
        # Step 1: Initial retrieval
        all_passages: list[str] = []
        initial_passages = self.retriever.retrieve(question)
        all_passages.extend(initial_passages)

        # Step 2: Iterative sub-query decomposition and retrieval
        for iteration in range(self.max_retrieval_iters - 1):
            if not all_passages:
                break

            context = "\n---\n".join(all_passages[:5])  # Use top passages for analysis
            prompt = SUBQUERY_DECOMPOSITION_PROMPT.format(
                question=question,
                context=context,
            )

            response, _ = self.client.chat_completion(
                model=self.gen_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=300,
            )

            # Parse sub-queries from JSON response
            try:
                # Strip markdown code fences if present
                cleaned = response.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
                sub_queries = json.loads(cleaned)
            except (json.JSONDecodeError, IndexError):
                break

            if not sub_queries or not isinstance(sub_queries, list):
                break

            # Retrieve for each sub-query
            new_passages_found = False
            for sub_q in sub_queries[:3]:  # Limit sub-queries
                new_passages = self.retriever.retrieve(sub_q, top_k=3)
                for p in new_passages:
                    if p not in all_passages:
                        all_passages.append(p)
                        new_passages_found = True

            if not new_passages_found:
                break  # No new information, stop iterating

        return all_passages

    def generate_answer(
        self, question: str, context: list[str]
    ) -> str:
        """Generate an answer using retrieved context.

        Args:
            question: The original question.
            context: List of retrieved passage texts.

        Returns:
            The generated answer string.
        """
        if context:
            context_str = "\n\n---\n\n".join(context)
            prompt = GENERATION_PROMPT.format(context=context_str, question=question)
        else:
            prompt = GENERATION_NO_CONTEXT_PROMPT.format(question=question)

        response, _ = self.client.chat_completion(
            model=self.gen_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.gen_temp,
            max_tokens=1000,
        )
        return response

    def check_hallucination(
        self, question: str, answer: str, context: list[str]
    ) -> dict:
        """Check if the answer is grounded in the retrieved context.

        Asks the LLM to evaluate whether every claim in the answer
        is supported by the provided passages.

        Args:
            question: The original question.
            answer: The generated answer to evaluate.
            context: The retrieved passages used for generation.

        Returns:
            Dictionary with keys ``is_grounded`` (bool),
            ``confidence`` (float), ``unsupported_claims`` (list),
            and ``suggested_refinement`` (str or None).
        """
        if not context:
            # No context to check against for no_retrieval tier
            return {
                "is_grounded": True,
                "confidence": 0.5,
                "unsupported_claims": [],
                "suggested_refinement": None,
            }

        context_str = "\n\n---\n\n".join(context)
        prompt = HALLUCINATION_CHECK_PROMPT.format(
            context=context_str,
            question=question,
            answer=answer,
        )

        response, _ = self.client.chat_completion(
            model=self.gen_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.hal_temp,
            max_tokens=500,
        )

        try:
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
            result = json.loads(cleaned)
        except (json.JSONDecodeError, IndexError):
            result = {
                "is_grounded": True,
                "confidence": 0.5,
                "unsupported_claims": [],
                "suggested_refinement": None,
            }

        return result

    def process_question(self, question: QuestionInput) -> QuestionResult:
        """Process a single question through the full Agentic RAG pipeline.

        Executes: classify → retrieve (dynamic) → generate → hallucination check.
        If the hallucination check fails, re-retrieves with a refined query
        and regenerates, up to ``max_hallucination_retries`` times.

        Args:
            question: The question to process.

        Returns:
            A :class:`QuestionResult` with answer, context, tokens, and metadata.
        """
        # Track per-question token usage via client snapshot
        start_usage = self.client.get_cumulative_usage()
        start_time = time.time()

        try:
            # --- Stage 1: Classify ---
            tier = self.classify_query(question.question)

            # --- Stage 2: Dynamic Retrieval ---
            if tier == "no_retrieval":
                context = []
            elif tier == "single_step":
                context = self.retrieve_single_step(question.question)
            else:  # multi_step
                context = self.retrieve_multi_step(question.question)

            # --- Stage 3: Generate ---
            answer = self.generate_answer(question.question, context)

            # --- Stage 4: Hallucination Check (only if we retrieved) ---
            hallucination_result = {"is_grounded": True, "confidence": 1.0}
            retries = 0

            if tier != "no_retrieval":
                for attempt in range(self.max_hal_retries + 1):
                    hal_check = self.check_hallucination(
                        question.question, answer, context
                    )
                    hallucination_result = hal_check

                    if hal_check.get("is_grounded", True):
                        break

                    retries += 1
                    # Re-retrieve with refined query
                    refined_query = hal_check.get("suggested_refinement")
                    if refined_query:
                        new_passages = self.retriever.retrieve(refined_query)
                        # Merge new passages with existing
                        for p in new_passages:
                            if p not in context:
                                context.append(p)
                        # Regenerate
                        answer = self.generate_answer(question.question, context)

            latency = time.time() - start_time

            # Compute per-question token delta
            end_usage = self.client.get_cumulative_usage()
            token_usage = TokenUsage(
                prompt_tokens=end_usage.prompt_tokens - start_usage.prompt_tokens,
                completion_tokens=end_usage.completion_tokens - start_usage.completion_tokens,
                total_tokens=end_usage.total_tokens - start_usage.total_tokens,
                embedding_tokens=end_usage.embedding_tokens - start_usage.embedding_tokens,
            )

        except Exception as e:
            latency = time.time() - start_time
            answer = f"[ERROR] {str(e)}"
            context = []
            tier = "error"
            hallucination_result = {}
            retries = 0
            token_usage = TokenUsage()

        return QuestionResult(
            question_id=question.id,
            input=question.question,
            retriever_context=context,
            output=answer,
            ground_truth=question.ground_truth,
            token_usage=token_usage,
            latency_seconds=round(latency, 3),
            metadata={
                "classification_tier": tier,
                "hallucination_check": hallucination_result,
                "hallucination_retries": retries,
            },
        )


# ============================================================================
# Main execution
# ============================================================================

def run_agentic_rag(
    questions_path: str | None = None,
    output_dir: str | None = None,
    max_workers: int | None = None,
) -> str:
    """Run the Agentic RAG approach on a question corpus.

    This is the main entry point for programmatic or CLI invocation.

    Args:
        questions_path: Path to the questions JSON file.
        output_dir: Directory for output files.
        max_workers: Max parallel workers.

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
    print(f"[AgenticRAG] Processing {len(questions)} questions (max_workers={max_workers})")

    runner = AgenticRAGRunner(cfg)
    results: list[QuestionResult] = []

    if max_workers <= 1:
        for i, q in enumerate(questions):
            print(f"  [{i+1}/{len(questions)}] {q.question[:80]}...")
            result = runner.process_question(q)
            results.append(result)
            tier = result.metadata.get("classification_tier", "?")
            print(f"    -> tier={tier}, {result.latency_seconds}s, {result.token_usage.total_tokens} tokens")
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
                tier = result.metadata.get("classification_tier", "?")
                print(f"  [{len(results)}/{len(questions)}] {q.id}: tier={tier}, {result.latency_seconds}s")

    results.sort(key=lambda r: r.question_id)

    total_usage = runner.client.get_cumulative_usage()

    output = ApproachOutput(
        approach="agentic_rag",
        timestamp=OutputLogger.get_timestamp(),
        model_config={
            "generation_model": cfg["models"]["generation_model"],
            "classifier_model": cfg["models"]["classifier_model"],
            "embedding_model": cfg["models"]["embedding_model"],
        },
        results=results,
        total_token_usage=total_usage,
    )

    logger = OutputLogger(output_dir)
    filepath = logger.save(output)
    return filepath


def main() -> None:
    """CLI entry point for the Agentic RAG approach."""
    parser = argparse.ArgumentParser(description="Run Agentic RAG on GDPR questions")
    parser.add_argument("--questions", type=str, help="Path to questions JSON")
    parser.add_argument("--output-dir", type=str, help="Output directory")
    parser.add_argument("--max-workers", type=int, default=1, help="Max parallel workers")
    args = parser.parse_args()

    filepath = run_agentic_rag(
        questions_path=args.questions,
        output_dir=args.output_dir,
        max_workers=args.max_workers,
    )
    print(f"[AgenticRAG] Done. Output: {filepath}")


if __name__ == "__main__":
    main()
