#!/usr/bin/env python3
"""
CRAG (Corrective Retrieval-Augmented Generation) for GDPR question answering.

Implements the Corrective RAG pattern from `Yan et al. (2024)
<https://arxiv.org/abs/2401.15884>`_, adapted for GDPR question answering
without external web search (all retrieval stays within the GDPR corpus).

Pipeline stages:

1. **Retrieve**: Fetch candidate passages from the shared ChromaDB collection.
2. **Grade**: An LLM evaluates each retrieved passage for relevance to the
   question, assigning a confidence score and a verdict (Correct / Incorrect /
   Ambiguous).
3. **Refine** (conditional):
   - *Correct* (high confidence): Use the retrieved passages directly and
     extract key knowledge strips.
   - *Ambiguous* (medium confidence): Combine original passages with
     results from a refined re-query.
   - *Incorrect* (low confidence): Discard originals, decompose the query
     into sub-questions, and re-retrieve.
4. **Generate**: Produce the final answer using the refined, high-quality
   context.

Usage:
    python approaches/crag/run.py [--questions PATH] [--output-dir PATH]

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

RELEVANCE_GRADING_PROMPT = """You are a relevance grader for a GDPR question-answering system. Evaluate whether the following passage is relevant to answering the given question.

Question: {question}

Passage:
{passage}

Evaluate the passage and respond with a JSON object:
{{
    "is_relevant": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation of why this passage is or isn't relevant"
}}

Evaluation:"""

KNOWLEDGE_STRIP_PROMPT = """Extract the key factual statements from the following GDPR passage that are relevant to the question. Return each statement as a separate item.

Question: {question}

Passage:
{passage}

Respond with a JSON array of concise knowledge strips:
["statement 1", "statement 2", ...]

Knowledge strips:"""

QUERY_REFINEMENT_PROMPT = """The following question was asked about GDPR, but the initial retrieval did not find sufficiently relevant passages.

Original question: {question}

The retrieved passages were not relevant enough. Please generate 2-3 refined search queries that might retrieve more relevant information from a GDPR corpus. Focus on specific GDPR articles, provisions, or legal concepts mentioned or implied in the question.

Respond with a JSON array of refined query strings:
["refined query 1", "refined query 2"]

Refined queries:"""

GENERATION_PROMPT = """You are a GDPR legal expert. Answer the following question based strictly on the provided knowledge context.

Knowledge Context:
{context}

Question: {question}

Provide a clear, accurate, and comprehensive answer. Base your response strictly on the provided context. If the context is insufficient, state what is available and what gaps exist.

Answer:"""


# ============================================================================
# ChromaDB Retriever (shared with Agentic RAG)
# ============================================================================

class ChromaRetriever:
    """Dense retriever backed by a persistent ChromaDB collection.

    Identical to the retriever in Agentic RAG — both approaches share
    the same ChromaDB collection and embedding model for fair comparison.

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

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
    ) -> list[str]:
        """Retrieve relevant passages for a query.

        Args:
            query: The search query text.
            top_k: Override for number of results.

        Returns:
            List of retrieved passage texts, ordered by relevance.
        """
        k = top_k or self.top_k
        embeddings, _ = self.client.embed(self.embedding_model, [query])

        results = self.collection.query(
            query_embeddings=embeddings,
            n_results=k,
            include=["documents", "distances"],
        )

        documents = results["documents"][0] if results["documents"] else []
        return documents


# ============================================================================
# CRAG Pipeline
# ============================================================================

class CRAGRunner:
    """Orchestrates the Corrective RAG pipeline.

    Implements retrieve → grade → refine → generate with configurable
    confidence thresholds for the grading stage.

    Attributes:
        client: Tracked OpenAI client for all LLM calls.
        retriever: ChromaDB retriever for passage lookup.
        config: Parsed settings dictionary.
        threshold_correct: Score above this → ``Correct``.
        threshold_ambiguous: Score above this (but below correct) → ``Ambiguous``.
    """

    def __init__(self, config: dict) -> None:
        """Initialize the CRAG pipeline.

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
        self.gen_temp = config["crag"]["generation_temperature"]
        self.threshold_correct = config["crag"]["relevance_threshold_correct"]
        self.threshold_ambiguous = config["crag"]["relevance_threshold_ambiguous"]
        self.max_refinements = config["crag"]["max_refinement_iterations"]

    def grade_passage(self, question: str, passage: str) -> dict:
        """Grade a single passage for relevance to the question.

        Args:
            question: The question to evaluate against.
            passage: The retrieved passage text.

        Returns:
            Dictionary with ``is_relevant`` (bool), ``confidence`` (float),
            and ``reasoning`` (str).
        """
        prompt = RELEVANCE_GRADING_PROMPT.format(
            question=question,
            passage=passage,
        )

        response, _ = self.client.chat_completion(
            model=self.gen_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=200,
        )

        try:
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
            result = json.loads(cleaned)
        except (json.JSONDecodeError, IndexError):
            result = {"is_relevant": True, "confidence": 0.5, "reasoning": "Parse error"}

        return result

    def grade_all_passages(
        self, question: str, passages: list[str]
    ) -> tuple[str, list[dict]]:
        """Grade all retrieved passages and determine the overall verdict.

        The overall verdict is determined by the average confidence score:
            - ``>= threshold_correct``: ``"correct"``
            - ``>= threshold_ambiguous``: ``"ambiguous"``
            - ``< threshold_ambiguous``: ``"incorrect"``

        Args:
            question: The question text.
            passages: List of retrieved passages to grade.

        Returns:
            A tuple of ``(verdict, grades)`` where verdict is one of
            ``"correct"``, ``"ambiguous"``, ``"incorrect"`` and grades
            is the list of per-passage grading results.
        """
        if not passages:
            return "incorrect", []

        grades = []
        for passage in passages:
            grade = self.grade_passage(question, passage)
            grades.append(grade)

        # Compute average confidence across all passages
        avg_confidence = sum(g.get("confidence", 0) for g in grades) / len(grades)

        if avg_confidence >= self.threshold_correct:
            verdict = "correct"
        elif avg_confidence >= self.threshold_ambiguous:
            verdict = "ambiguous"
        else:
            verdict = "incorrect"

        return verdict, grades

    def extract_knowledge_strips(
        self, question: str, passages: list[str]
    ) -> list[str]:
        """Extract key factual statements from relevant passages.

        Implements the knowledge refinement step from CRAG, distilling
        verbose passages into concise knowledge strips for generation.

        Args:
            question: The question for context.
            passages: Passages to extract knowledge from.

        Returns:
            List of concise factual statements.
        """
        all_strips = []
        for passage in passages:
            prompt = KNOWLEDGE_STRIP_PROMPT.format(
                question=question, passage=passage
            )
            response, _ = self.client.chat_completion(
                model=self.gen_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=500,
            )
            try:
                cleaned = response.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
                strips = json.loads(cleaned)
                if isinstance(strips, list):
                    all_strips.extend(strips)
            except (json.JSONDecodeError, IndexError):
                # Fallback: use the passage itself
                all_strips.append(passage)

        return all_strips

    def refine_and_retrieve(self, question: str) -> list[str]:
        """Generate refined queries and re-retrieve from the corpus.

        Used when initial retrieval is judged as ``"incorrect"`` or
        as a supplement for ``"ambiguous"`` verdicts.

        Args:
            question: The original question.

        Returns:
            List of passages retrieved via refined queries.
        """
        prompt = QUERY_REFINEMENT_PROMPT.format(question=question)
        response, _ = self.client.chat_completion(
            model=self.gen_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=300,
        )

        try:
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
            refined_queries = json.loads(cleaned)
        except (json.JSONDecodeError, IndexError):
            refined_queries = [question]  # Fallback to original

        new_passages = []
        for rq in refined_queries[:3]:
            passages = self.retriever.retrieve(rq, top_k=3)
            for p in passages:
                if p not in new_passages:
                    new_passages.append(p)

        return new_passages

    def generate_answer(self, question: str, context: list[str]) -> str:
        """Generate an answer from the refined context.

        Args:
            question: The original question.
            context: List of knowledge strips or passages.

        Returns:
            The generated answer string.
        """
        if context:
            context_str = "\n\n".join(f"- {item}" for item in context)
        else:
            context_str = "[No relevant context found]"

        prompt = GENERATION_PROMPT.format(context=context_str, question=question)

        response, _ = self.client.chat_completion(
            model=self.gen_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.gen_temp,
            max_tokens=1000,
        )
        return response

    def process_question(self, question: QuestionInput) -> QuestionResult:
        """Process a single question through the full CRAG pipeline.

        Executes: retrieve → grade → (refine if needed) → generate.

        Args:
            question: The question to process.

        Returns:
            A :class:`QuestionResult` with answer, context, tokens, and metadata.
        """
        start_usage = self.client.get_cumulative_usage()
        start_time = time.time()

        try:
            # --- Stage 1: Initial Retrieval ---
            initial_passages = self.retriever.retrieve(question.question)

            # --- Stage 2: Grade ---
            verdict, grades = self.grade_all_passages(
                question.question, initial_passages
            )

            # --- Stage 3: Refine based on verdict ---
            refinement_iterations = 0
            all_context: list[str] = []

            if verdict == "correct":
                # High confidence: extract knowledge strips from relevant passages
                relevant_passages = [
                    p for p, g in zip(initial_passages, grades)
                    if g.get("is_relevant", True)
                ]
                knowledge_strips = self.extract_knowledge_strips(
                    question.question, relevant_passages or initial_passages
                )
                all_context = knowledge_strips

            elif verdict == "ambiguous":
                # Medium confidence: use initial passages + refined retrieval
                all_context = list(initial_passages)
                for iteration in range(self.max_refinements):
                    refined_passages = self.refine_and_retrieve(question.question)
                    for p in refined_passages:
                        if p not in all_context:
                            all_context.append(p)
                    refinement_iterations += 1
                    # Re-grade the combined context
                    new_verdict, _ = self.grade_all_passages(
                        question.question, all_context
                    )
                    if new_verdict == "correct":
                        break

            else:  # incorrect
                # Low confidence: discard originals, try refined retrieval
                for iteration in range(self.max_refinements):
                    refined_passages = self.refine_and_retrieve(question.question)
                    all_context.extend(
                        p for p in refined_passages if p not in all_context
                    )
                    refinement_iterations += 1
                    if all_context:
                        new_verdict, _ = self.grade_all_passages(
                            question.question, all_context
                        )
                        if new_verdict in ("correct", "ambiguous"):
                            break

            # --- Stage 4: Generate ---
            answer = self.generate_answer(question.question, all_context)

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
            all_context = []
            verdict = "error"
            grades = []
            refinement_iterations = 0
            token_usage = TokenUsage()

        return QuestionResult(
            question_id=question.id,
            input=question.question,
            retriever_context=all_context,
            output=answer,
            ground_truth=question.ground_truth,
            token_usage=token_usage,
            latency_seconds=round(latency, 3),
            metadata={
                "initial_verdict": verdict,
                "passage_grades": grades,
                "refinement_iterations": refinement_iterations,
                "final_context_count": len(all_context),
            },
        )


# ============================================================================
# Main execution
# ============================================================================

def run_crag(
    questions_path: str | None = None,
    output_dir: str | None = None,
    max_workers: int | None = None,
) -> str:
    """Run the CRAG approach on a question corpus.

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
    print(f"[CRAG] Processing {len(questions)} questions (max_workers={max_workers})")

    runner = CRAGRunner(cfg)
    results: list[QuestionResult] = []

    if max_workers <= 1:
        for i, q in enumerate(questions):
            print(f"  [{i+1}/{len(questions)}] {q.question[:80]}...")
            result = runner.process_question(q)
            results.append(result)
            verdict = result.metadata.get("initial_verdict", "?")
            print(f"    -> verdict={verdict}, {result.latency_seconds}s, {result.token_usage.total_tokens} tokens")
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
                verdict = result.metadata.get("initial_verdict", "?")
                print(f"  [{len(results)}/{len(questions)}] {q.id}: verdict={verdict}, {result.latency_seconds}s")

    results.sort(key=lambda r: r.question_id)

    total_usage = runner.client.get_cumulative_usage()

    output = ApproachOutput(
        approach="crag",
        timestamp=OutputLogger.get_timestamp(),
        model_config={
            "generation_model": cfg["models"]["generation_model"],
            "embedding_model": cfg["models"]["embedding_model"],
        },
        results=results,
        total_token_usage=total_usage,
    )

    logger = OutputLogger(output_dir)
    filepath = logger.save(output)
    return filepath


def main() -> None:
    """CLI entry point for the CRAG approach."""
    parser = argparse.ArgumentParser(description="Run CRAG on GDPR questions")
    parser.add_argument("--questions", type=str, help="Path to questions JSON")
    parser.add_argument("--output-dir", type=str, help="Output directory")
    parser.add_argument("--max-workers", type=int, default=1, help="Max parallel workers")
    args = parser.parse_args()

    filepath = run_crag(
        questions_path=args.questions,
        output_dir=args.output_dir,
        max_workers=args.max_workers,
    )
    print(f"[CRAG] Done. Output: {filepath}")


if __name__ == "__main__":
    main()
