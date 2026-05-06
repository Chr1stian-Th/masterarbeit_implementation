#!/usr/bin/env python3
"""
Merge retry evaluation results into the original results file.

Replaces errored entries (``errored: true``) in the original results with
the corresponding entries from a partial retry results file produced by
``run_retry_evaluation.py``. Recalculates per-metric aggregate statistics
(average_score, pass_rate, passed count) after patching.

Writes a new merged results file — the originals are never modified.

Usage:
    python evaluation/merge_results.py \\
        --original  results/eval_agentic_rag_<timestamp>.json \\
        --patch     results/retry/retry_eval_agentic_rag_<timestamp>.json \\
        --output    results/merged_eval_agentic_rag_<timestamp>.json

If --output is omitted, the merged file is written next to --original with
a "merged_" prefix.
"""

import os
import json
import argparse
from datetime import datetime, timezone


def _recalc_metric_stats(metric_data: dict) -> None:
    scores = metric_data["per_question_scores"]
    scoreable = [s for s in scores if s.get("passed") is not None]
    passed_count = sum(1 for s in scores if s.get("passed") is True)
    avg = sum(s["score"] for s in scores) / len(scores) if scores else 0.0
    metric_data["average_score"] = round(avg, 4)
    metric_data["pass_rate"] = round(passed_count / len(scoreable), 4) if scoreable else 0.0
    metric_data["total_cases"] = len(scores)
    metric_data["passed"] = passed_count


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Merge retry evaluation results into the original results file"
    )
    parser.add_argument(
        "--original",
        required=True,
        help="Original evaluation results JSON file (contains errored entries)",
    )
    parser.add_argument(
        "--patch",
        required=True,
        help="Partial retry results JSON produced by run_retry_evaluation.py",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output path for merged results (default: merged_<original_filename>)",
    )
    args = parser.parse_args()

    with open(args.original, "r", encoding="utf-8") as f:
        original = json.load(f)
    with open(args.patch, "r", encoding="utf-8") as f:
        patch = json.load(f)

    partial_metrics: dict = patch.get("partial_metrics", {})
    if not partial_metrics:
        print("No partial_metrics found in patch file — nothing to merge.")
        return

    patched_count = 0
    still_errored = 0

    for metric_name, retry_scores in partial_metrics.items():
        if metric_name not in original["metrics"]:
            print(f"WARNING: metric '{metric_name}' not in original — skipping")
            continue

        retry_by_qid = {s["question_id"]: s for s in retry_scores}
        orig_scores = original["metrics"][metric_name]["per_question_scores"]

        for i, entry in enumerate(orig_scores):
            qid = entry["question_id"]
            if entry.get("errored") and qid in retry_by_qid:
                new_entry = retry_by_qid[qid]
                orig_scores[i] = new_entry
                if new_entry.get("errored"):
                    still_errored += 1
                    print(f"  {metric_name}/{qid}: still errored — kept new error entry")
                else:
                    patched_count += 1
                    print(f"  {metric_name}/{qid}: patched (score={new_entry['score']:.4f})")

        _recalc_metric_stats(original["metrics"][metric_name])

    # Rebuild per_question combined view
    scores_by_metric_by_qid: dict = {}
    for metric_name, metric_data in original["metrics"].items():
        scores_by_metric_by_qid[metric_name] = {
            s["question_id"]: s for s in metric_data["per_question_scores"]
        }

    for pq_entry in original.get("per_question", []):
        qid = pq_entry["question_id"]
        for metric_name in original["metrics"]:
            if qid in scores_by_metric_by_qid.get(metric_name, {}):
                pq_entry["metrics"][metric_name] = scores_by_metric_by_qid[metric_name][qid]

    original["merged_from_retry"] = os.path.basename(args.patch)
    original["merge_timestamp"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    if args.output:
        out_path = args.output
    else:
        orig_dir = os.path.dirname(args.original)
        orig_name = os.path.basename(args.original)
        out_path = os.path.join(orig_dir, f"merged_{orig_name}")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(original, f, indent=2, ensure_ascii=False)

    print(f"\nMerged {patched_count} entries ({still_errored} still errored).")
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
