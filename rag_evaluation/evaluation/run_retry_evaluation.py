#!/usr/bin/env python3
"""
Re-evaluate only the (metric, question) pairs that errored in a previous run.

Reads an errors manifest (produced alongside a filtered output file) and the
original RAG output file, then runs each failed metric only on the questions
that errored for it. Saves a partial results file that can be merged back into
the original results with ``merge_results.py``.

Usage:
    python evaluation/run_retry_evaluation.py \\
        --output-file outputs/retry_agentic_rag_<timestamp>.json \\
        --errors-manifest outputs/errors_manifest_agentic_rag_<timestamp>.json \\
        --results-dir results/retry/ \\
        [--model gpt-4o-mini]
"""

import os
import sys
import json
import argparse
from datetime import datetime, timezone

EVAL_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(EVAL_DIR, ".."))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, EVAL_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(EVAL_DIR, ".env"))

from deepeval.test_case import LLMTestCase
from metrics import get_metric

import yaml as _yaml
def _load_settings() -> dict:
    config_path = os.path.join(PROJECT_ROOT, "config", "settings.yaml")
    if not os.path.exists(config_path):
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return _yaml.safe_load(f) or {}

_CFG = _load_settings()
_EVAL_CFG = _CFG.get("evaluation", {})
_DEFAULT_JUDGE_MODEL: str = _EVAL_CFG.get("judge_model", "gpt-4o-mini")
_DEFAULT_THRESHOLDS: dict = _EVAL_CFG.get("thresholds", {})

from evaluate import _measure_with_retry, TokenUsageTracker


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Retry evaluation for previously errored (metric, question) pairs"
    )
    parser.add_argument(
        "--output-file",
        required=True,
        help="Filtered RAG output JSON (the retry_<approach>_<timestamp>.json file)",
    )
    parser.add_argument(
        "--errors-manifest",
        required=True,
        help="Errors manifest JSON (errors_manifest_<approach>_<timestamp>.json)",
    )
    parser.add_argument(
        "--results-dir",
        required=True,
        help="Directory to write the partial retry results file",
    )
    parser.add_argument(
        "--model",
        default=_DEFAULT_JUDGE_MODEL,
        help="Judge model for LLM-as-judge metrics (default from settings.yaml)",
    )
    args = parser.parse_args()

    with open(args.output_file, "r", encoding="utf-8") as f:
        output_data = json.load(f)
    with open(args.errors_manifest, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    approach = output_data.get("approach", "unknown")
    errored_by_metric: dict[str, list[str]] = manifest["errored_by_metric"]

    # Index results by question_id for fast lookup
    results_by_qid = {r["question_id"]: r for r in output_data["results"]}

    os.makedirs(args.results_dir, exist_ok=True)
    token_tracker = TokenUsageTracker()
    token_tracker.install()

    partial_metrics: dict = {}

    try:
        for metric_name, errored_qids in errored_by_metric.items():
            print(f"\n[Retry] Metric: {metric_name} — {len(errored_qids)} question(s) to retry")

            kwargs: dict = {"model": args.model}
            if metric_name in _DEFAULT_THRESHOLDS:
                kwargs["threshold"] = _DEFAULT_THRESHOLDS[metric_name]
            metric = get_metric(metric_name, **kwargs)

            token_tracker.set_context(approach, metric_name)
            metric_scores = []

            for qid in errored_qids:
                if qid not in results_by_qid:
                    print(f"  WARNING: {qid} not found in output file — skipping")
                    continue

                r = results_by_qid[qid]
                tc = LLMTestCase(
                    input=r["input"],
                    actual_output=r["output"],
                    expected_output=r.get("ground_truth", ""),
                    retrieval_context=r.get("retriever_context", []),
                )

                score, reason, errored = _measure_with_retry(metric, tc)
                threshold = getattr(metric, "threshold", None)
                passed = False if errored else (score >= threshold if threshold is not None else None)

                record: dict = {
                    "question_id": qid,
                    "score": score,
                    "reason": reason,
                    "passed": passed,
                }
                if errored:
                    record["errored"] = True

                metric_scores.append(record)
                status = "ERROR" if errored else f"score={score:.4f}"
                print(f"  {qid}: {status}")

            partial_metrics[metric_name] = metric_scores

    finally:
        token_tracker.uninstall()
        token_report = token_tracker.compile_report(model=args.model)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
        token_path = os.path.join(args.results_dir, f"token_usage_retry_{timestamp}.json")
        with open(token_path, "w", encoding="utf-8") as f:
            json.dump(token_report, f, indent=2)
        overview = token_report["overview"]
        print(
            f"\n[Retry] Token usage — prompt: {overview['prompt_tokens']:,}, "
            f"completion: {overview['completion_tokens']:,}, "
            f"total: {overview['total_tokens']:,} ({overview['api_calls']} API calls)"
        )

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
    partial_results = {
        "approach": approach,
        "source_output_file": manifest["source_output_file"],
        "source_results_file": manifest["source_results_file"],
        "retry_timestamp": timestamp,
        "model": args.model,
        "partial_metrics": partial_metrics,
    }

    out_path = os.path.join(args.results_dir, f"retry_eval_{approach}_{timestamp}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(partial_results, f, indent=2, ensure_ascii=False)
    print(f"\n[Retry] Partial results saved: {out_path}")
    print("Next step: merge with original using merge_results.py")


if __name__ == "__main__":
    main()
