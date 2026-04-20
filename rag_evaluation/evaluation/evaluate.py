#!/usr/bin/env python3
"""
Evaluation framework for RAG approach outputs using DeepEval.

Reads output JSON files produced by the RAG approaches, constructs
DeepEval test cases, runs all registered metrics against them, and
writes structured evaluation results to the results directory.

The framework is designed to be extensible: add new metrics by creating
modules in ``evaluation/metrics/`` (see :mod:`evaluation.metrics` for
the registry pattern).

Usage:
    # Evaluate all outputs with all metrics
    python evaluation/evaluate.py --input-dir outputs/ --output-dir results/

    # Evaluate only a specific approach (e.g., 'lightrag', 'agentic_rag', 'crag')
    python evaluation/evaluate.py --input-dir outputs/ --output-dir results/ --filter lightrag

    # Evaluate with specific metrics only
    python evaluation/evaluate.py --input-dir outputs/ --output-dir results/ --metrics faithfulness

    # List available metrics
    python evaluation/evaluate.py --list-metrics

Environment Variables:
    OPENAI_API_KEY: Required. Used by DeepEval for LLM-as-judge metrics.
"""

import os
import sys
import json
import glob
import argparse
import time
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
EVAL_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(EVAL_DIR, ".."))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, EVAL_DIR)

# Load evaluation .env
load_dotenv(os.path.join(EVAL_DIR, ".env"))

from deepeval.test_case import LLMTestCase

from metrics import get_metric, list_metrics


# ============================================================================
# Token Usage Tracking
# ============================================================================

class TokenUsageTracker:
    """Tracks OpenAI API token usage by patching the openai Completions class.

    Patches ``openai.resources.chat.completions.Completions.create`` and its
    async counterpart so that every API call made by DeepEval metrics is
    recorded, keyed by (approach, metric).

    Usage::

        tracker = TokenUsageTracker()
        tracker.install()
        tracker.set_context("lightrag", "faithfulness")
        # ... run metric ...
        tracker.uninstall()
        report = tracker.compile_report(model="gpt-4o-mini")
    """

    def __init__(self) -> None:
        self._usage: dict[str, dict[str, dict[str, int]]] = {}
        self._current_approach: str | None = None
        self._current_metric: str | None = None
        self._original_create: Any = None
        self._original_acreate: Any = None

    def set_context(self, approach: str, metric: str) -> None:
        """Set the current (approach, metric) context for attribution."""
        self._current_approach = approach
        self._current_metric = metric

    def _record(self, usage: Any) -> None:
        if not self._current_approach or not self._current_metric or not usage:
            return
        approach_data = self._usage.setdefault(self._current_approach, {})
        metric_data = approach_data.setdefault(
            self._current_metric,
            {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "api_calls": 0},
        )
        metric_data["prompt_tokens"] += getattr(usage, "prompt_tokens", 0) or 0
        metric_data["completion_tokens"] += getattr(usage, "completion_tokens", 0) or 0
        metric_data["total_tokens"] += getattr(usage, "total_tokens", 0) or 0
        metric_data["api_calls"] += 1

    def install(self) -> None:
        """Patch the OpenAI client classes to intercept usage data."""
        try:
            import openai.resources.chat.completions as _completions_mod
        except ImportError:
            return

        tracker = self
        Completions = _completions_mod.Completions
        AsyncCompletions = _completions_mod.AsyncCompletions

        original_create = Completions.create
        self._original_create = original_create

        def _patched_create(self_client, *args, **kwargs):
            response = original_create(self_client, *args, **kwargs)
            if hasattr(response, "usage"):
                tracker._record(response.usage)
            return response

        Completions.create = _patched_create

        try:
            original_acreate = AsyncCompletions.create
            self._original_acreate = original_acreate

            async def _patched_acreate(self_client, *args, **kwargs):
                response = await original_acreate(self_client, *args, **kwargs)
                if hasattr(response, "usage"):
                    tracker._record(response.usage)
                return response

            AsyncCompletions.create = _patched_acreate
        except Exception:
            pass

    def uninstall(self) -> None:
        """Restore the original OpenAI client methods."""
        try:
            import openai.resources.chat.completions as _completions_mod
        except ImportError:
            return

        if self._original_create is not None:
            _completions_mod.Completions.create = self._original_create
        if self._original_acreate is not None:
            _completions_mod.AsyncCompletions.create = self._original_acreate

    def compile_report(self, model: str = "") -> dict:
        """Build a structured token-usage report from collected data.

        The report contains:

        - ``by_approach``: per-approach breakdown with per-metric detail and
          approach-level totals.
        - ``by_metric``: per-metric view with per-approach detail and
          metric-level totals.
        - ``overview``: grand totals across all approaches and metrics.

        Args:
            model: The judge model name used during evaluation (for context).

        Returns:
            A JSON-serialisable dictionary with the full token-usage report.
        """
        def _zero() -> dict:
            return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "api_calls": 0}

        def _add(acc: dict, src: dict) -> None:
            for key in ("prompt_tokens", "completion_tokens", "total_tokens", "api_calls"):
                acc[key] = acc.get(key, 0) + src.get(key, 0)

        by_approach: dict = {}
        by_metric: dict = {}
        overview = _zero()

        for approach, metrics in self._usage.items():
            approach_totals = _zero()
            approach_entry: dict = {"by_metric": {}, "totals": approach_totals}

            for metric, counts in metrics.items():
                approach_entry["by_metric"][metric] = dict(counts)
                _add(approach_totals, counts)

                metric_entry = by_metric.setdefault(metric, {"by_approach": {}, "totals": _zero()})
                metric_entry["by_approach"][approach] = dict(counts)
                _add(metric_entry["totals"], counts)

            by_approach[approach] = approach_entry
            _add(overview, approach_totals)

        return {
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
            "judge_model": model,
            "by_approach": by_approach,
            "by_metric": by_metric,
            "overview": overview,
        }

# ============================================================================
# Retry / Checkpoint Helpers
# ============================================================================

_RETRYABLE_PATTERNS = ("429", "500", "502", "503", "504", "timeout", "connection", "rate limit")


def _measure_with_retry(
    metric,
    tc,
    max_retries: int = 3,
    base_delay: float = 2.0,
) -> tuple:
    """Call metric.measure with exponential backoff on transient errors.

    Returns (score, reason, errored: bool).
    """
    last_exc: Exception | None = None
    for attempt in range(max_retries):
        try:
            metric.measure(tc)
            return metric.score, getattr(metric, "reason", None), False
        except Exception as exc:
            last_exc = exc
            err_lower = str(exc).lower()
            retryable = any(p in err_lower for p in _RETRYABLE_PATTERNS)
            if retryable and attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                print(f"      [retry {attempt + 1}/{max_retries - 1}] {str(exc)[:100]} — waiting {delay:.0f}s")
                time.sleep(delay)
            else:
                break
    return 0.0, f"Error: {last_exc}", True


def _checkpoint_path(checkpoint_dir: str, approach: str) -> str:
    return os.path.join(checkpoint_dir, f"ckpt_{approach}.json")


def _load_checkpoint(checkpoint_dir: str, approach: str) -> dict:
    """Load {metric_name: {question_id: score_record}} from disk, or {}."""
    path = _checkpoint_path(checkpoint_dir, approach)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_checkpoint(checkpoint_dir: str, approach: str, data: dict) -> None:
    """Atomically write checkpoint to disk."""
    os.makedirs(checkpoint_dir, exist_ok=True)
    path = _checkpoint_path(checkpoint_dir, approach)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp, path)


def _delete_checkpoint(checkpoint_dir: str, approach: str) -> None:
    try:
        os.remove(_checkpoint_path(checkpoint_dir, approach))
    except FileNotFoundError:
        pass


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------
import yaml as _yaml

def _load_settings() -> dict:
    """Load settings.yaml from the project config directory."""
    config_path = os.path.join(PROJECT_ROOT, "config", "settings.yaml")
    if not os.path.exists(config_path):
        return {}
    with open(config_path, "r", encoding="utf-8") as _f:
        return _yaml.safe_load(_f) or {}

_CFG = _load_settings()
_EVAL_CFG = _CFG.get("evaluation", {})
_DEFAULT_JUDGE_MODEL: str = _EVAL_CFG.get("judge_model", "gpt-4o-mini")
_DEFAULT_THRESHOLDS: dict = _EVAL_CFG.get("thresholds", {})


# ============================================================================
# Output File Loading
# ============================================================================

def load_approach_outputs(
    input_dir: str,
    filter_approach: str | None = None,
) -> list[dict]:
    """Load all approach output JSON files from a directory.

    Args:
        input_dir: Directory containing output JSON files.
        filter_approach: If set, only load files whose ``approach``
            field matches this string.

    Returns:
        List of parsed output dictionaries, one per approach run.
    """
    json_files = sorted(glob.glob(os.path.join(input_dir, "*.json")))

    if not json_files:
        print(f"[Evaluate] No JSON files found in {input_dir}")
        return []

    outputs = []
    for filepath in json_files:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        if filter_approach and data.get("approach") != filter_approach:
            continue

        data["_source_file"] = os.path.basename(filepath)
        outputs.append(data)

    print(f"[Evaluate] Loaded {len(outputs)} output file(s) from {input_dir}")
    return outputs


# ============================================================================
# Test Case Construction
# ============================================================================

def build_test_cases(output: dict) -> list[LLMTestCase]:
    """Convert an approach output into DeepEval test cases.

    Each question result becomes one :class:`LLMTestCase` with:
        - ``input``: The original question
        - ``actual_output``: The generated answer
        - ``expected_output``: The ground truth answer
        - ``retrieval_context``: The retrieved passages

    Args:
        output: Parsed approach output dictionary.

    Returns:
        List of :class:`LLMTestCase` instances.
    """
    test_cases = []
    for result in output.get("results", []):
        tc = LLMTestCase(
            input=result["input"],
            actual_output=result["output"],
            expected_output=result.get("ground_truth", ""),
            retrieval_context=result.get("retriever_context", []),
        )
        test_cases.append(tc)
    return test_cases


# ============================================================================
# Evaluation Runner
# ============================================================================

def run_evaluation(
    input_dir: str,
    output_dir: str,
    filter_approach: str | None = None,
    metric_names: list[str] | None = None,
    model: str = _DEFAULT_JUDGE_MODEL,
) -> dict:
    """Run DeepEval metrics on approach outputs and save results.

    For each approach output file:
        1. Build test cases from the output results.
        2. Run all (or specified) metrics against each test case.
        3. Collect scores, reasons, and pass/fail status.
        4. Save a structured JSON report in the output directory.

    Args:
        input_dir: Directory containing approach output JSON files.
        output_dir: Directory to write evaluation result files.
        filter_approach: Optional filter to evaluate a single approach.
        metric_names: Optional list of specific metric names to run.
            If ``None``, all registered metrics are used.
        model: OpenAI model for LLM-as-judge metrics.

    Returns:
        Dictionary mapping approach names to their evaluation results.
    """
    os.makedirs(output_dir, exist_ok=True)
    checkpoint_dir = os.path.join(output_dir, "checkpoints")

    # Session-level timestamp used for all output filenames in this run
    session_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")

    # Install token tracker before any metric calls
    token_tracker = TokenUsageTracker()
    token_tracker.install()

    all_results: dict = {}

    try:
        # Load outputs
        outputs = load_approach_outputs(input_dir, filter_approach)
        if not outputs:
            print("[Evaluate] No outputs to evaluate.")
            return {}

        # Initialize metrics — pass per-metric thresholds from config when available
        def _metric_kwargs(name: str) -> dict:
            kwargs: dict = {"model": model}
            if name in _DEFAULT_THRESHOLDS:
                kwargs["threshold"] = _DEFAULT_THRESHOLDS[name]
            return kwargs

        if metric_names:
            metrics_dict = {name: get_metric(name, **_metric_kwargs(name)) for name in metric_names}
        else:
            metrics_dict = {}
            from metrics import list_metrics as _list_metrics
            for name in _list_metrics():
                metrics_dict[name] = get_metric(name, **_metric_kwargs(name))

        if not metrics_dict:
            print("[Evaluate] No metrics registered. Add metrics to evaluation/metrics/.")
            return {}

        print(f"[Evaluate] Running metrics: {list(metrics_dict.keys())}")

        for output in outputs:
            approach = output.get("approach", "unknown")
            source_file = output.get("_source_file", "unknown.json")
            print(f"\n[Evaluate] Evaluating: {approach} ({source_file})")

            test_cases = build_test_cases(output)
            if not test_cases:
                print(f"  No test cases for {approach}")
                continue

            # Load checkpoint — resumes a previously interrupted run
            checkpoint = _load_checkpoint(checkpoint_dir, approach)
            if any(checkpoint.values()):
                completed = sum(len(v) for v in checkpoint.values())
                print(f"  [resume] Checkpoint found — {completed} question×metric result(s) already scored.")

            approach_results = {
                "approach": approach,
                "source_file": source_file,
                "evaluation_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
                "model_config": output.get("model_config", {}),
                "metrics": {},
                "per_question": [],
            }

            for metric_name, metric in metrics_dict.items():
                print(f"  Running metric: {metric_name}...")

                metric_checkpoint = checkpoint.setdefault(metric_name, {})
                metric_scores = []

                token_tracker.set_context(approach, metric_name)

                for i, tc in enumerate(test_cases):
                    q_id = output["results"][i].get("question_id", f"q{i}")

                    if q_id in metric_checkpoint:
                        # Reuse previously saved result — no API call needed
                        metric_scores.append(metric_checkpoint[q_id])
                        continue

                    score, reason, errored = _measure_with_retry(metric, tc)
                    threshold = getattr(metric, "threshold", None)
                    if errored:
                        passed = False
                    elif threshold is not None:
                        passed = score >= threshold
                    else:
                        passed = None

                    record: dict = {
                        "question_id": q_id,
                        "score": score,
                        "reason": reason,
                        "passed": passed,
                    }
                    if errored:
                        record["errored"] = True

                    metric_scores.append(record)
                    metric_checkpoint[q_id] = record
                    _save_checkpoint(checkpoint_dir, approach, checkpoint)

                metric_passes = sum(1 for s in metric_scores if s["passed"] is True)
                avg_score = (
                    sum(s["score"] for s in metric_scores) / len(metric_scores)
                    if metric_scores else 0.0
                )
                scoreable_cases = [s for s in metric_scores if s["passed"] is not None]
                approach_results["metrics"][metric_name] = {
                    "average_score": round(avg_score, 4),
                    "pass_rate": round(metric_passes / len(scoreable_cases), 4) if scoreable_cases else 0.0,
                    "total_cases": len(metric_scores),
                    "passed": metric_passes,
                    "threshold": getattr(metric, "threshold", None),
                    "per_question_scores": metric_scores,
                }

                print(f"    {metric_name}: avg={avg_score:.4f}, pass_rate={metric_passes}/{len(metric_scores)}")

            # Build per-question combined view
            for i, result in enumerate(output.get("results", [])):
                question_eval = {
                    "question_id": result.get("question_id", f"q{i}"),
                    "input": result.get("input", ""),
                    "output": result.get("output", ""),
                    "ground_truth": result.get("ground_truth", ""),
                    "metrics": {},
                }
                for metric_name, metric_data in approach_results["metrics"].items():
                    if i < len(metric_data["per_question_scores"]):
                        question_eval["metrics"][metric_name] = metric_data["per_question_scores"][i]
                approach_results["per_question"].append(question_eval)

            # Save results and clean up checkpoint on success
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
            result_filename = f"eval_{approach}_{timestamp}.json"
            result_path = os.path.join(output_dir, result_filename)

            with open(result_path, "w", encoding="utf-8") as f:
                json.dump(approach_results, f, indent=2, ensure_ascii=False)

            _delete_checkpoint(checkpoint_dir, approach)
            print(f"  Saved: {result_path}")
            all_results[approach] = approach_results

        # Save summary across all approaches
        if len(all_results) > 1:
            summary = {
                "evaluation_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
                "approaches_evaluated": list(all_results.keys()),
                "comparative_summary": {},
            }

            for metric_name in metrics_dict.keys():
                comparison = {}
                for approach, result in all_results.items():
                    if metric_name in result["metrics"]:
                        comparison[approach] = {
                            "average_score": result["metrics"][metric_name]["average_score"],
                            "pass_rate": result["metrics"][metric_name]["pass_rate"],
                        }
                summary["comparative_summary"][metric_name] = comparison

            summary_path = os.path.join(output_dir, f"summary_evaluation_{session_timestamp}.json")
            with open(summary_path, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            print(f"\n[Evaluate] Comparative summary: {summary_path}")

    finally:
        # Always uninstall the tracker and persist the token report, even on crash
        token_tracker.uninstall()
        token_report = token_tracker.compile_report(model=model)
        token_report_path = os.path.join(output_dir, f"token_usage_evaluation_{session_timestamp}.json")
        with open(token_report_path, "w", encoding="utf-8") as f:
            json.dump(token_report, f, indent=2, ensure_ascii=False)
        overview = token_report["overview"]
        print(
            f"\n[Evaluate] Token usage — prompt: {overview['prompt_tokens']:,}, "
            f"completion: {overview['completion_tokens']:,}, "
            f"total: {overview['total_tokens']:,} "
            f"({overview['api_calls']} API calls)"
        )
        print(f"[Evaluate] Token usage report: {token_report_path}")

    return all_results


# ============================================================================
# CLI Entry Point
# ============================================================================

def main() -> None:
    """Command-line interface for the evaluation framework."""
    parser = argparse.ArgumentParser(
        description="Evaluate RAG approach outputs using DeepEval metrics"
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default=os.path.join(PROJECT_ROOT, "outputs"),
        help="Directory containing approach output JSON files",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=os.path.join(PROJECT_ROOT, "results"),
        help="Directory to write evaluation results",
    )
    parser.add_argument(
        "--filter",
        type=str,
        default=None,
        help="Evaluate only a specific approach (e.g., 'lightrag', 'agentic_rag', 'crag')",
    )
    parser.add_argument(
        "--metrics",
        type=str,
        nargs="+",
        default=None,
        help="Specific metrics to run (e.g., 'faithfulness'). Default: all",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=_DEFAULT_JUDGE_MODEL,
        help="OpenAI model for LLM-as-judge metrics (default from evaluation.judge_model in settings.yaml)",
    )
    parser.add_argument(
        "--list-metrics",
        action="store_true",
        help="List all available metrics and exit",
    )
    args = parser.parse_args()

    if args.list_metrics:
        available = list_metrics()
        print("Available metrics:")
        for name in available:
            print(f"  - {name}")
        return

    run_evaluation(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        filter_approach=args.filter,
        metric_names=args.metrics,
        model=args.model,
    )


if __name__ == "__main__":
    main()
