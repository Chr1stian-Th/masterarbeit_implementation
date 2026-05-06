#!/usr/bin/env python3
"""
Create a filtered output file and errors manifest for retrying failed evaluations.

Given an original RAG output file and an evaluation results file, this script:
1. Extracts all (metric, question_id) pairs marked with ``errored: true``
2. Writes a filtered output file containing only those questions (same schema
   as the original — usable directly as input for ``run_retry_evaluation.py``)
3. Writes an errors manifest mapping each metric to its failed question IDs

Usage:
    python evaluation/create_retry_input.py \\
        --output-file  outputs/agentic_rag_<timestamp>.json \\
        --results-file results/eval_agentic_rag_<timestamp>.json \\
        [--out-dir     outputs/]

Output files are written to --out-dir (defaults to the same directory as
--output-file) with the naming convention:
    retry_<original_output_filename>
    errors_manifest_<original_output_filename>
"""

import os
import json
import argparse


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Produce a filtered retry output file and errors manifest from existing results"
    )
    parser.add_argument(
        "--output-file",
        required=True,
        help="Original RAG output JSON file (e.g. outputs/agentic_rag_<timestamp>.json)",
    )
    parser.add_argument(
        "--results-file",
        required=True,
        help="Evaluation results JSON file containing errored entries (e.g. results/eval_agentic_rag_<timestamp>.json)",
    )
    parser.add_argument(
        "--out-dir",
        default=None,
        help="Directory to write output files (default: same directory as --output-file)",
    )
    args = parser.parse_args()

    with open(args.output_file, "r", encoding="utf-8") as f:
        output_data = json.load(f)
    with open(args.results_file, "r", encoding="utf-8") as f:
        results_data = json.load(f)

    # Collect errored question IDs per metric
    errored_by_metric: dict[str, list[str]] = {}
    for metric_name, metric_data in results_data.get("metrics", {}).items():
        errored = [
            s["question_id"]
            for s in metric_data.get("per_question_scores", [])
            if s.get("errored")
        ]
        if errored:
            errored_by_metric[metric_name] = errored

    if not errored_by_metric:
        print("No errored entries found in results file — nothing to do.")
        return

    all_errored_qids = set(qid for qids in errored_by_metric.values() for qid in qids)

    print(f"Found errors in {len(errored_by_metric)} metric(s) across {len(all_errored_qids)} unique question(s):")
    for metric, qids in errored_by_metric.items():
        print(f"  {metric} ({len(qids)}): {qids}")

    # Filtered output file — same schema, only errored questions
    filtered_results = [
        r for r in output_data.get("results", [])
        if r["question_id"] in all_errored_qids
    ]

    missing = all_errored_qids - {r["question_id"] for r in filtered_results}
    if missing:
        print(f"\nWARNING: {len(missing)} errored question(s) not found in output file: {sorted(missing)}")

    filtered_output = {k: v for k, v in output_data.items() if k != "results"}
    filtered_output["results"] = filtered_results

    out_dir = args.out_dir or os.path.dirname(os.path.abspath(args.output_file))
    os.makedirs(out_dir, exist_ok=True)

    base_name = os.path.basename(args.output_file)
    retry_path = os.path.join(out_dir, f"retry_{base_name}")
    manifest_path = os.path.join(out_dir, f"errors_manifest_{base_name}")

    with open(retry_path, "w", encoding="utf-8") as f:
        json.dump(filtered_output, f, indent=2, ensure_ascii=False)

    manifest = {
        "source_output_file": base_name,
        "source_results_file": os.path.basename(args.results_file),
        "approach": output_data.get("approach"),
        "errored_by_metric": errored_by_metric,
        "all_errored_question_ids": sorted(all_errored_qids),
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"\nFiltered output ({len(filtered_results)} questions): {retry_path}")
    print(f"Errors manifest: {manifest_path}")
    print("\nNext step:")
    print(f"  python evaluation/run_retry_evaluation.py \\")
    print(f"      --output-file  {retry_path} \\")
    print(f"      --errors-manifest {manifest_path} \\")
    print(f"      --results-dir  <results_dir>/retry/")


if __name__ == "__main__":
    main()
