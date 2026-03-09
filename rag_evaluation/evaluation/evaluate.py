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
from datetime import datetime, timezone

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
        # get_all_metrics passes the same kwargs to every factory; build a
        # combined set using the first threshold found (metrics with their own
        # thresholds in config will be handled individually below).
        metrics_dict = {}
        from metrics import list_metrics as _list_metrics
        for name in _list_metrics():
            metrics_dict[name] = get_metric(name, **_metric_kwargs(name))

    if not metrics_dict:
        print("[Evaluate] No metrics registered. Add metrics to evaluation/metrics/.")
        return {}

    print(f"[Evaluate] Running metrics: {list(metrics_dict.keys())}")

    all_results = {}

    for output in outputs:
        approach = output.get("approach", "unknown")
        source_file = output.get("_source_file", "unknown.json")
        print(f"\n[Evaluate] Evaluating: {approach} ({source_file})")

        test_cases = build_test_cases(output)
        if not test_cases:
            print(f"  No test cases for {approach}")
            continue

        # Run each metric on all test cases
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

            metric_scores = []
            metric_passes = 0

            for i, tc in enumerate(test_cases):
                try:
                    metric.measure(tc)
                    score = metric.score
                    reason = getattr(metric, "reason", None)
                    threshold = getattr(metric, "threshold", None)
                    passed = (score >= threshold) if threshold is not None else None
                except Exception as e:
                    score = 0.0
                    reason = f"Error: {str(e)}"
                    passed = False

                if passed is True:
                    metric_passes += 1

                metric_scores.append({
                    "question_id": output["results"][i].get("question_id", f"q{i}"),
                    "score": score,
                    "reason": reason,
                    "passed": passed,
                })

            avg_score = (
                sum(s["score"] for s in metric_scores) / len(metric_scores)
                if metric_scores
                else 0.0
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
                    question_eval["metrics"][metric_name] = (
                        metric_data["per_question_scores"][i]
                    )
            approach_results["per_question"].append(question_eval)

        # Save results
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
        result_filename = f"eval_{approach}_{timestamp}.json"
        result_path = os.path.join(output_dir, result_filename)

        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(approach_results, f, indent=2, ensure_ascii=False)

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

        summary_path = os.path.join(output_dir, f"summary_{timestamp}.json")
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"\n[Evaluate] Comparative summary: {summary_path}")

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
