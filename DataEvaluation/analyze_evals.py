#!/usr/bin/env python3
"""
Evaluation Analysis Script
==========================

Analyzes eval_*.json files produced by a RAG evaluation pipeline and produces
comparison graphs across models, approaches, and metrics.

USAGE
-----
    python analyze_evals.py \\
        --eval-dir path/to/eval_jsons/ \\
        --questions classified_questions.json \\
        [--costs costs.json] \\
        [--output-dir analysis_output]

INPUTS
------
* --eval-dir   : folder containing eval_<approach>_<timestamp>.json files.
                 Each file is expected to have:
                   - "approach"                       (str)
                   - "model_config.generation_model"  (str) -> the "model"
                   - "source_file"                    (str, sibling filename)
                   - "metrics"                        (dict of metric -> summary)
                   - "per_question"                   (list of {question_id, input,
                                                       output, metrics: {metric:
                                                       {score, passed, errored?}}})
* --questions  : classified_questions.json -- list of objects with at least
                 "id", "domain", "difficulty", "answer_type", "ai_act_relevant".
                 Joined onto eval rows by question_id == id.
* --costs      : optional costs.json (see "COST CONFIG" below).
* --output-dir : where to save figures (default: ./analysis_output).

COST CONFIG
-----------
The script computes raw cost (USD) and "average score per dollar" using a
costs.json file. Expected format:

    {
        "google/gemini-3-flash-preview": {
            "input_per_1m": 0.10,
            "output_per_1m": 0.40
        },
        "openai/gpt-5": {
            "input_per_1m": 1.25,
            "output_per_1m": 10.00
        }
    }

Token counts are read from the file referenced by `source_file` inside each
eval file, expected to live in the SAME folder as the eval (or, if absolute,
at the path given). Each per-question entry of the source file should expose
a `usage` (or `tokens`) object with `input_tokens`/`output_tokens` (alternative
names accepted: `prompt_tokens`/`completion_tokens`).

If the source file or usage data is missing, the script falls back to a rough
estimate: 4 chars/token of input/output text + a fixed input overhead for
system prompt and retrieved context. Tune the ESTIMATE_* constants below if
your prompts/contexts are notably larger or smaller.

OUTPUTS
-------
output_dir/
├── all_metrics/    comparisons across all metrics in one figure
├── per_metric/     one figure per metric
├── cost/           raw cost and score-per-dollar charts
└── breakdowns/     scores broken down by domain / difficulty / answer_type
"""

from __future__ import annotations

import argparse
import datetime
import json
import warnings
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Fallback token estimation when usage data is unavailable. Adjust to taste.
CHARS_PER_TOKEN = 4
ESTIMATE_INPUT_OVERHEAD_TOKENS = 500  # ~system prompt + retrieved context

# Score types to plot. The user wanted both.
SCORE_TYPES = ["avg_score", "pass_rate"]

# Difficulty bucketing for breakdowns
DIFFICULTY_BUCKETS = [
    (-0.01, 0.25, "easy (≤0.25)"),
    (0.25, 0.50, "medium (0.25–0.5)"),
    (0.50, 0.75, "hard (0.5–0.75)"),
    (0.75, 1.01, "very hard (>0.75)"),
]

# Default figure sizes
FIG_WIDE = (12, 6)
FIG_NARROW = (8, 5)

# Use a clean style
plt.rcParams.update({
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "grid.linestyle": "--",
    "figure.dpi": 110,
})


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_eval_files(eval_dir: Path) -> list[dict]:
    """Load every eval_*.json in ``eval_dir``."""
    files = sorted(eval_dir.glob("eval_*.json"))
    if not files:
        raise FileNotFoundError(f"No eval_*.json files in {eval_dir}")
    evals = []
    for f in files:
        with open(f) as fh:
            data = json.load(fh)
        data["_path"] = f
        # Validate required fields, warn if missing
        approach = data.get("approach")
        model = data.get("model_config", {}).get("generation_model")
        if not approach:
            warnings.warn(f"{f.name}: missing 'approach' — using 'unknown'.")
        if not model:
            warnings.warn(f"{f.name}: missing model_config.generation_model — using 'unknown'.")
        evals.append(data)
    return evals


def load_classified_questions(path: Path) -> dict[str, dict]:
    """Load classified_questions.json and index by id."""
    with open(path) as fh:
        items = json.load(fh)
    return {q["id"]: q for q in items}


def load_costs(path: Path | None) -> dict:
    """Load costs.json if provided."""
    if path is None or not path.exists():
        if path is not None:
            warnings.warn(f"Costs file {path} not found — cost charts will be skipped.")
        return {}
    with open(path) as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# DataFrame construction
# ---------------------------------------------------------------------------

def build_long_dataframe(evals: list[dict], classified_by_id: dict[str, dict]) -> pd.DataFrame:
    """One row per (model, approach, question, metric); errored entries excluded."""
    rows = []
    for ev in evals:
        approach = ev.get("approach", "unknown")
        model = ev.get("model_config", {}).get("generation_model", "unknown")
        for pq in ev.get("per_question", []):
            qid = pq["question_id"]
            classified = classified_by_id.get(qid, {})
            for metric_name, metric_data in pq.get("metrics", {}).items():
                # Drop errored entries entirely (per user instructions)
                if metric_data.get("errored", False):
                    continue
                rows.append({
                    "model": model,
                    "approach": approach,
                    "model_approach": f"{model} | {approach}",
                    "question_id": qid,
                    "metric": metric_name,
                    "score": float(metric_data.get("score", np.nan)),
                    "passed": bool(metric_data.get("passed", False)),
                    "domain": classified.get("domain"),
                    "difficulty": classified.get("difficulty"),
                    "answer_type": classified.get("answer_type"),
                    "ai_act_relevant": classified.get("ai_act_relevant"),
                })
    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError("No usable rows after filtering errored entries.")

    # Difficulty bucket label
    if "difficulty" in df.columns:
        df["difficulty_bucket"] = pd.cut(
            df["difficulty"],
            bins=[b[0] for b in DIFFICULTY_BUCKETS] + [DIFFICULTY_BUCKETS[-1][1]],
            labels=[b[2] for b in DIFFICULTY_BUCKETS],
            include_lowest=True,
        )
    return df


# ---------------------------------------------------------------------------
# Cost computation
# ---------------------------------------------------------------------------

def _extract_usage(item: dict) -> tuple[int | None, int | None]:
    """Try several common shapes for usage data."""
    usage = item.get("usage") or item.get("tokens") or {}
    if not isinstance(usage, dict):
        return None, None
    in_t = usage.get("input_tokens") or usage.get("prompt_tokens")
    out_t = usage.get("output_tokens") or usage.get("completion_tokens")
    return in_t, out_t


def compute_costs(evals: list[dict], costs_table: dict, eval_dir: Path) -> pd.DataFrame:
    """Build a DataFrame of total tokens + USD cost per (model, approach)."""
    rows = []
    for ev in evals:
        model = ev.get("model_config", {}).get("generation_model", "unknown")
        approach = ev.get("approach", "unknown")
        pricing = costs_table.get(model)
        if pricing is None:
            warnings.warn(
                f"No pricing for model '{model}' — cost will be NaN for "
                f"({model}, {approach})."
            )

        # Try to load source file for real token counts
        source_name = ev.get("source_file", "")
        source_path = (eval_dir / source_name) if source_name else None
        src_data = None
        if source_path and source_path.exists():
            try:
                with open(source_path) as fh:
                    src_data = json.load(fh)
            except Exception as e:
                warnings.warn(f"Could not read {source_path}: {e}")

        total_in = 0
        total_out = 0
        used_estimate = False

        usage_items: list[dict] = []
        if isinstance(src_data, dict):
            for key in ("per_question", "results", "items", "questions"):
                cand = src_data.get(key)
                if isinstance(cand, list):
                    usage_items = cand
                    break
        elif isinstance(src_data, list):
            usage_items = src_data

        found_any = False
        for it in usage_items:
            if not isinstance(it, dict):
                continue
            in_t, out_t = _extract_usage(it)
            if in_t is not None and out_t is not None:
                total_in += int(in_t)
                total_out += int(out_t)
                found_any = True

        if not found_any:
            # Fallback: estimate from text lengths.
            used_estimate = True
            for pq in ev.get("per_question", []):
                inp = pq.get("input", "") or ""
                out = pq.get("output", "") or ""
                total_in += ESTIMATE_INPUT_OVERHEAD_TOKENS + len(inp) // CHARS_PER_TOKEN
                total_out += len(out) // CHARS_PER_TOKEN
            warnings.warn(
                f"({model}, {approach}): no usage data found, using estimated "
                f"token counts (in≈{total_in}, out≈{total_out})."
            )

        if pricing:
            cost_usd = (
                total_in * pricing["input_per_1m"]
                + total_out * pricing["output_per_1m"]
            ) / 1_000_000
        else:
            cost_usd = float("nan")

        rows.append({
            "model": model,
            "approach": approach,
            "model_approach": f"{model} | {approach}",
            "input_tokens": total_in,
            "output_tokens": total_out,
            "cost_usd": cost_usd,
            "used_estimate": used_estimate,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Aggregation helpers
# ---------------------------------------------------------------------------

def aggregate(df: pd.DataFrame, group_cols: list[str], score_type: str) -> pd.DataFrame:
    """Aggregate scores with 95% CI half-width; score_type ∈ {avg_score, pass_rate}."""
    col = "score" if score_type == "avg_score" else "passed"

    def _ci95(x):
        arr = np.asarray(x, dtype=float)
        n = len(arr)
        if n < 2:
            return 0.0
        se = arr.std(ddof=1) / np.sqrt(n)
        return float(se * stats.t.ppf(0.975, df=n - 1))

    agg = (
        df.groupby(group_cols, dropna=False)[col]
        .agg(value="mean", ci=_ci95, n="count")
        .reset_index()
    )
    return agg


def score_label(score_type: str) -> str:
    return "Avg score" if score_type == "avg_score" else "Pass rate"


# ---------------------------------------------------------------------------
# Plotting helpers
# ---------------------------------------------------------------------------

def _bar_pivot(pivot: pd.DataFrame, ax, ylabel: str, title: str, ylim=(0, 1.05),
               errors: pd.DataFrame | None = None):
    pivot.plot(kind="bar", ax=ax, edgecolor="black", linewidth=0.4, width=0.8,
               yerr=errors, error_kw={"linewidth": 1, "ecolor": "black", "capsize": 3})
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    if ylim is not None:
        ax.set_ylim(*ylim)
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    ax.legend(loc="best", fontsize=8, frameon=False)


def plot_all_metrics_grouped(df: pd.DataFrame, group_col: str, score_type: str,
                             save_path: Path):
    """Grouped bars: x = metric, hue = group_col."""
    agg = aggregate(df, ["metric", group_col], score_type)
    pivot = agg.pivot(index="metric", columns=group_col, values="value")
    errors = agg.pivot(index="metric", columns=group_col, values="ci")
    fig, ax = plt.subplots(figsize=FIG_WIDE)
    title = f"All metrics — {score_label(score_type)} by {group_col}"
    _bar_pivot(pivot, ax, score_label(score_type), title, errors=errors)
    plt.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)


def plot_all_metrics_facets(df: pd.DataFrame, facet_col: str, group_col: str,
                            score_type: str, save_path: Path):
    """One subplot per facet_col value; bars on x = metric, hue = group_col."""
    facet_values = sorted(df[facet_col].unique())
    n = len(facet_values)
    if n == 0:
        return
    cols = min(2, n)
    rows = int(np.ceil(n / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(7 * cols, 4.5 * rows), squeeze=False)
    for i, fv in enumerate(facet_values):
        ax = axes[i // cols][i % cols]
        sub = df[df[facet_col] == fv]
        agg = aggregate(sub, ["metric", group_col], score_type)
        pivot = agg.pivot(index="metric", columns=group_col, values="value")
        errors = agg.pivot(index="metric", columns=group_col, values="ci")
        title = f"{fv} — {score_label(score_type)}"
        _bar_pivot(pivot, ax, score_label(score_type), title, errors=errors)
    # Hide unused subplots
    for j in range(n, rows * cols):
        axes[j // cols][j % cols].axis("off")
    fig.suptitle(f"All metrics by {group_col}, faceted per {facet_col}",
                 fontsize=12, y=1.02)
    plt.tight_layout()
    fig.savefig(save_path, bbox_inches="tight")
    plt.close(fig)


def plot_per_metric_bars(df: pd.DataFrame, metric: str, group_col: str,
                         score_type: str, save_path: Path):
    """Bar chart for a single metric, x = group_col."""
    sub = df[df["metric"] == metric]
    agg = aggregate(sub, [group_col], score_type)
    fig, ax = plt.subplots(figsize=FIG_NARROW)
    xs = agg[group_col].astype(str).tolist()
    colors = plt.cm.tab10(np.linspace(0, 0.9, max(len(xs), 1)))
    ax.bar(xs, agg["value"], yerr=agg["ci"], capsize=4,
           color=colors, edgecolor="black", linewidth=0.4,
           error_kw={"linewidth": 1, "ecolor": "black"})
    ax.set_title(f"{metric} — {score_label(score_type)} by {group_col}")
    ax.set_ylabel(score_label(score_type))
    ax.set_ylim(0, 1.05)
    ax.set_xticks(range(len(xs)))
    ax.set_xticklabels(xs, rotation=30, ha="right")
    plt.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)


def plot_per_metric_facets(df: pd.DataFrame, metric: str, facet_col: str,
                           group_col: str, score_type: str, save_path: Path):
    """Per-metric, one subplot per facet_col value, bars by group_col."""
    sub = df[df["metric"] == metric]
    facet_values = sorted(sub[facet_col].unique())
    n = len(facet_values)
    if n == 0:
        return
    cols = min(3, n)
    rows = int(np.ceil(n / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 4 * rows), squeeze=False)
    for i, fv in enumerate(facet_values):
        ax = axes[i // cols][i % cols]
        s2 = sub[sub[facet_col] == fv]
        agg = aggregate(s2, [group_col], score_type)
        xs = agg[group_col].astype(str).tolist()
        colors = plt.cm.tab10(np.linspace(0, 0.9, max(len(xs), 1)))
        ax.bar(xs, agg["value"], yerr=agg["ci"], capsize=4,
               color=colors, edgecolor="black", linewidth=0.4,
               error_kw={"linewidth": 1, "ecolor": "black"})
        ax.set_title(f"{fv}")
        ax.set_ylabel(score_label(score_type))
        ax.set_ylim(0, 1.05)
        ax.set_xticks(range(len(xs)))
        ax.set_xticklabels(xs, rotation=30, ha="right")
    for j in range(n, rows * cols):
        axes[j // cols][j % cols].axis("off")
    fig.suptitle(f"{metric} — {score_label(score_type)} by {group_col}, "
                 f"per {facet_col}", fontsize=12, y=1.02)
    plt.tight_layout()
    fig.savefig(save_path, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Spider / radar charts
# ---------------------------------------------------------------------------

def plot_spider_chart(df: pd.DataFrame, group_col: str, score_type: str,
                      save_path: Path):
    """Radar chart: axes = metrics, one polygon per group_col value."""
    agg = aggregate(df, ["metric", group_col], score_type)
    metrics = sorted(agg["metric"].unique())
    groups = sorted(agg[group_col].unique())
    N = len(metrics)
    if N < 3:
        return  # need ≥3 axes for a meaningful radar chart

    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]  # close the polygon

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    colors = plt.cm.tab10(np.linspace(0, 0.9, max(len(groups), 1)))

    for group, color in zip(groups, colors):
        vals = []
        cis = []
        for metric in metrics:
            row = agg[(agg["metric"] == metric) & (agg[group_col] == group)]
            vals.append(float(row["value"].iloc[0]) if not row.empty else 0.0)
            cis.append(float(row["ci"].iloc[0]) if not row.empty else 0.0)
        vals += vals[:1]
        cis += cis[:1]

        ax.plot(angles, vals, "o-", linewidth=2, color=color, label=str(group))
        ax.fill(angles, vals, alpha=0.1, color=color)

        # CI band
        ci_upper = [min(v + c, 1.0) for v, c in zip(vals, cis)]
        ci_lower = [max(v - c, 0.0) for v, c in zip(vals, cis)]
        ax.fill_between(angles, ci_lower, ci_upper, alpha=0.08, color=color)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metrics, fontsize=9)
    ax.set_ylim(0, 1)
    ax.set_title(f"All metrics — {score_label(score_type)} by {group_col}",
                 pad=20, fontsize=12)
    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.1), fontsize=8,
              frameon=False)
    plt.tight_layout()
    fig.savefig(save_path, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Cost plots
# ---------------------------------------------------------------------------

def plot_cost_charts(cost_df: pd.DataFrame, df_scores: pd.DataFrame, save_dir: Path):
    if cost_df.empty or cost_df["cost_usd"].isna().all():
        warnings.warn("No usable cost data — skipping cost charts.")
        return

    # 1) Raw cost per (model, approach)
    fig, ax = plt.subplots(figsize=FIG_NARROW)
    plot_df = cost_df.dropna(subset=["cost_usd"])
    colors = plt.cm.tab10(np.linspace(0, 0.9, max(len(plot_df), 1)))
    ax.bar(plot_df["model_approach"], plot_df["cost_usd"],
           color=colors, edgecolor="black", linewidth=0.4)
    ax.set_title("Raw cost (USD) per model & approach")
    ax.set_ylabel("USD")
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    plt.tight_layout()
    fig.savefig(save_dir / "raw_cost_by_model_approach.png")
    plt.close(fig)

    # 2) Raw cost per model (sum over approaches)
    by_model = cost_df.groupby("model")["cost_usd"].sum(min_count=1).reset_index()
    by_model = by_model.dropna()
    if not by_model.empty:
        fig, ax = plt.subplots(figsize=FIG_NARROW)
        colors = plt.cm.tab10(np.linspace(0, 0.9, max(len(by_model), 1)))
        ax.bar(by_model["model"], by_model["cost_usd"],
               color=colors, edgecolor="black", linewidth=0.4)
        ax.set_title("Raw cost (USD) per model")
        ax.set_ylabel("USD")
        plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
        plt.tight_layout()
        fig.savefig(save_dir / "raw_cost_by_model.png")
        plt.close(fig)

    # 3) Raw cost per approach
    by_app = cost_df.groupby("approach")["cost_usd"].sum(min_count=1).reset_index()
    by_app = by_app.dropna()
    if not by_app.empty:
        fig, ax = plt.subplots(figsize=FIG_NARROW)
        colors = plt.cm.tab10(np.linspace(0, 0.9, max(len(by_app), 1)))
        ax.bar(by_app["approach"], by_app["cost_usd"],
               color=colors, edgecolor="black", linewidth=0.4)
        ax.set_title("Raw cost (USD) per approach")
        ax.set_ylabel("USD")
        plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
        plt.tight_layout()
        fig.savefig(save_dir / "raw_cost_by_approach.png")
        plt.close(fig)

    # 4) Avg-score-per-dollar overall, per (model, approach)
    avg_overall = (df_scores
                   .groupby(["model", "approach", "model_approach"])["score"]
                   .mean()
                   .reset_index())
    merged = avg_overall.merge(cost_df[["model_approach", "cost_usd"]],
                               on="model_approach", how="left")
    merged["score_per_usd"] = merged["score"] / merged["cost_usd"]
    plot_df = merged.dropna(subset=["score_per_usd"])
    if not plot_df.empty:
        fig, ax = plt.subplots(figsize=FIG_NARROW)
        colors = plt.cm.tab10(np.linspace(0, 0.9, max(len(plot_df), 1)))
        ax.bar(plot_df["model_approach"], plot_df["score_per_usd"],
               color=colors, edgecolor="black", linewidth=0.4)
        ax.set_title("Avg score per USD (overall)")
        ax.set_ylabel("score / USD")
        plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
        plt.tight_layout()
        fig.savefig(save_dir / "score_per_usd_overall.png")
        plt.close(fig)

    # 5) Score-per-dollar per metric, hue = model_approach
    avg_per_metric = (df_scores
                      .groupby(["model_approach", "metric"])["score"]
                      .mean()
                      .reset_index())
    merged_m = avg_per_metric.merge(cost_df[["model_approach", "cost_usd"]],
                                    on="model_approach", how="left")
    merged_m["score_per_usd"] = merged_m["score"] / merged_m["cost_usd"]
    plot_df = merged_m.dropna(subset=["score_per_usd"])
    if not plot_df.empty:
        pivot = plot_df.pivot(index="metric", columns="model_approach",
                              values="score_per_usd")
        fig, ax = plt.subplots(figsize=FIG_WIDE)
        pivot.plot(kind="bar", ax=ax, edgecolor="black", linewidth=0.4, width=0.8)
        ax.set_title("Avg score per USD, per metric")
        ax.set_ylabel("score / USD")
        plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
        ax.legend(loc="best", fontsize=8, frameon=False)
        plt.tight_layout()
        fig.savefig(save_dir / "score_per_usd_per_metric.png")
        plt.close(fig)

    # 6) Token mix (input vs output) stacked
    fig, ax = plt.subplots(figsize=FIG_NARROW)
    x = cost_df["model_approach"]
    ax.bar(x, cost_df["input_tokens"], label="input tokens",
           edgecolor="black", linewidth=0.4)
    ax.bar(x, cost_df["output_tokens"], bottom=cost_df["input_tokens"],
           label="output tokens", edgecolor="black", linewidth=0.4)
    ax.set_title("Token usage per model & approach")
    ax.set_ylabel("Tokens")
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    ax.legend(loc="best", fontsize=8, frameon=False)
    plt.tight_layout()
    fig.savefig(save_dir / "token_usage.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Breakdowns using classified_questions (domain / difficulty / answer_type)
# ---------------------------------------------------------------------------

def plot_breakdown(df: pd.DataFrame, breakdown_col: str, save_dir: Path):
    """One figure per breakdown column: grid of metrics, hue = model_approach."""
    if breakdown_col not in df.columns:
        return
    sub = df.dropna(subset=[breakdown_col])
    if sub.empty:
        return
    metrics = sorted(sub["metric"].unique())
    bucket_order = sorted(sub[breakdown_col].dropna().unique(),
                          key=lambda x: str(x))

    cols = 3
    rows = int(np.ceil(len(metrics) / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(6 * cols, 4 * rows), squeeze=False)
    for i, metric in enumerate(metrics):
        ax = axes[i // cols][i % cols]
        m_df = sub[sub["metric"] == metric]
        agg = aggregate(m_df, [breakdown_col, "model_approach"], "avg_score")
        try:
            pivot = agg.pivot(index=breakdown_col, columns="model_approach",
                              values="value").reindex(bucket_order)
            errors = agg.pivot(index=breakdown_col, columns="model_approach",
                               values="ci").reindex(bucket_order)
        except Exception:
            continue
        pivot.plot(kind="bar", ax=ax, edgecolor="black", linewidth=0.4, width=0.8,
                   yerr=errors, error_kw={"linewidth": 1, "ecolor": "black", "capsize": 3})
        ax.set_title(metric)
        ax.set_ylabel("Avg score")
        ax.set_ylim(0, 1.05)
        plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
        ax.legend(loc="best", fontsize=7, frameon=False)
    for j in range(len(metrics), rows * cols):
        axes[j // cols][j % cols].axis("off")
    fig.suptitle(f"Avg score broken down by {breakdown_col}",
                 fontsize=13, y=1.01)
    plt.tight_layout()
    fig.savefig(save_dir / f"by_{breakdown_col}.png", bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def _md_table(df: pd.DataFrame) -> str:
    """Render a DataFrame as a GitHub-flavored Markdown table."""
    def _cell(v) -> str:
        if isinstance(v, float):
            return "N/A" if np.isnan(v) else f"{v:.4f}"
        return str(v).replace("|", "\\|")

    cols = list(df.columns)
    header = "| " + " | ".join(cols) + " |"
    sep    = "| " + " | ".join(":---" for _ in cols) + " |"
    rows   = ["| " + " | ".join(_cell(v) for v in row) + " |"
              for _, row in df.iterrows()]
    return "\n".join([header, sep] + rows)


def _pivot_table(agg: pd.DataFrame, index_col: str, pivot_col: str) -> str:
    """Pivot agg into a markdown table; cells = 'mean ± ci (n=N)'."""
    agg = agg.copy()
    agg["_cell"] = agg.apply(
        lambda r: f"{r['value']:.3f} ± {r['ci']:.3f} (n={int(r['n'])})", axis=1
    )
    pivot = agg.pivot(index=index_col, columns=pivot_col, values="_cell").reset_index()
    pivot.columns.name = None
    # convert Categorical index to str so _md_table handles it cleanly
    pivot[index_col] = pivot[index_col].astype(str)
    return _md_table(pivot)


def _flat_table(agg: pd.DataFrame, group_col: str) -> str:
    """Flat markdown table with mean, ±CI, n columns."""
    out = agg[[group_col, "value", "ci", "n"]].copy()
    out["value"] = out["value"].map(lambda v: f"{v:.4f}")
    out["ci"]    = out["ci"].map(lambda v: f"{v:.4f}")
    out["n"]     = out["n"].astype(int)
    return _md_table(out.rename(columns={"value": "mean", "ci": "± CI (95%)"}))


def generate_report(
    df: pd.DataFrame,
    cost_df: pd.DataFrame | None,
    output_dir: Path,
) -> None:
    """Write report.md with tables of the numbers behind every figure."""
    lines: list[str] = []
    add = lines.append

    add("# Evaluation Analysis Report\n")
    add(f"_Generated: {datetime.date.today()}_\n")

    # ------------------------------------------------------------------
    # 1. Dataset Overview
    # ------------------------------------------------------------------
    add("## Dataset Overview\n")
    models    = sorted(df["model"].unique())
    approaches = sorted(df["approach"].unique())
    metrics   = sorted(df["metric"].unique())

    add("| Property | Value |")
    add("| :--- | :--- |")
    add(f"| Models | {', '.join(models)} |")
    add(f"| Approaches | {', '.join(approaches)} |")
    add(f"| Metrics | {', '.join(metrics)} |")
    add(f"| Unique questions | {df['question_id'].nunique()} |")
    add(f"| Scored rows (question × metric) | {len(df)} |\n")

    add("### Question Count per Model × Approach\n")
    q_counts = (
        df.groupby(["model", "approach"])["question_id"]
        .nunique()
        .reset_index()
        .rename(columns={"question_id": "unique_questions"})
    )
    add(_md_table(q_counts) + "\n")

    # ------------------------------------------------------------------
    # 2. Score Summaries
    # ------------------------------------------------------------------
    add("## Score Summaries\n")
    add("> Values: **mean ± 95 % CI (n = number of scored question–metric pairs)**.\n")

    for score_type in SCORE_TYPES:
        label = score_label(score_type)
        add(f"### {label}\n")

        add("#### By Model\n")
        agg = aggregate(df, ["metric", "model"], score_type)
        add(_pivot_table(agg, "metric", "model") + "\n")

        add("#### By Approach\n")
        agg = aggregate(df, ["metric", "approach"], score_type)
        add(_pivot_table(agg, "metric", "approach") + "\n")

        add("#### By Model × Approach (all metrics pooled)\n")
        agg = aggregate(df, ["model_approach"], score_type)
        add(_flat_table(agg, "model_approach") + "\n")

    # ------------------------------------------------------------------
    # 3. Per-Metric Results
    # ------------------------------------------------------------------
    add("## Per-Metric Results\n")

    for metric in metrics:
        add(f"### {metric}\n")
        sub = df[df["metric"] == metric]
        for score_type in SCORE_TYPES:
            add(f"#### {score_label(score_type)}\n")
            agg = aggregate(sub, ["model_approach"], score_type)
            add(_flat_table(agg, "model_approach") + "\n")

    # ------------------------------------------------------------------
    # 4. Cost Analysis
    # ------------------------------------------------------------------
    if cost_df is not None and not cost_df.empty:
        add("## Cost Analysis\n")

        add("### Token Usage and Raw Cost\n")
        tbl = cost_df[["model", "approach", "input_tokens", "output_tokens",
                        "cost_usd", "used_estimate"]].copy()
        tbl["used_estimate"] = tbl["used_estimate"].map(
            {True: "estimated", False: "actual"}
        )
        add(_md_table(tbl) + "\n")

        avg_overall = (
            df.groupby(["model", "approach", "model_approach"])["score"]
            .mean()
            .reset_index()
        )
        merged = avg_overall.merge(
            cost_df[["model_approach", "cost_usd"]], on="model_approach", how="left"
        )
        merged["score_per_usd"] = merged["score"] / merged["cost_usd"]
        spd = merged.dropna(subset=["score_per_usd"])
        if not spd.empty:
            add("### Score per Dollar\n")
            tbl2 = spd[["model_approach", "score", "cost_usd", "score_per_usd"]].rename(
                columns={"score": "avg_score", "cost_usd": "cost (USD)",
                         "score_per_usd": "score / USD"}
            )
            add(_md_table(tbl2) + "\n")

    # ------------------------------------------------------------------
    # 5. Breakdowns
    # ------------------------------------------------------------------
    add("## Breakdowns\n")
    add("> Values: **avg score ± 95 % CI (n)**.\n")

    for col in ("domain", "difficulty_bucket", "answer_type"):
        if col not in df.columns:
            continue
        sub = df.dropna(subset=[col])
        if sub.empty:
            continue
        add(f"### By {col.replace('_', ' ').title()}\n")
        for metric in metrics:
            add(f"#### {metric}\n")
            m_df = sub[sub["metric"] == metric]
            agg = aggregate(m_df, [col, "model_approach"], "avg_score")
            try:
                add(_pivot_table(agg, col, "model_approach") + "\n")
            except Exception:
                add("_(table generation failed for this breakdown)_\n")

    report_path = output_dir / "report.md"
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print(f"Report written to: {report_path.resolve()}")


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def make_all_plots(df: pd.DataFrame, output_dir: Path):
    """Generate the score-based figures requested by the user."""
    all_dir = output_dir / "all_metrics"
    per_dir = output_dir / "per_metric"
    all_dir.mkdir(parents=True, exist_ok=True)
    per_dir.mkdir(parents=True, exist_ok=True)

    metrics = sorted(df["metric"].unique())
    n_models = df["model"].nunique()
    n_approaches = df["approach"].nunique()

    for score_type in SCORE_TYPES:
        # 1) All metrics, by model
        plot_all_metrics_grouped(df, "model", score_type,
                                 all_dir / f"{score_type}_by_model.png")
        plot_spider_chart(df, "model", score_type,
                          all_dir / f"{score_type}_spider_by_model.png")
        # 2) All metrics, by approach
        plot_all_metrics_grouped(df, "approach", score_type,
                                 all_dir / f"{score_type}_by_approach.png")
        plot_spider_chart(df, "approach", score_type,
                          all_dir / f"{score_type}_spider_by_approach.png")
        # 3) All metrics, approaches per model + models per approach
        if n_models > 1:
            plot_all_metrics_facets(df, "model", "approach", score_type,
                                    all_dir / f"{score_type}_approaches_per_model.png")
        if n_approaches > 1:
            plot_all_metrics_facets(df, "approach", "model", score_type,
                                    all_dir / f"{score_type}_models_per_approach.png")

        # 4 + 5 + 6) Per-metric figures
        for metric in metrics:
            safe = metric.replace("/", "_")
            plot_per_metric_bars(df, metric, "model", score_type,
                                 per_dir / f"{safe}_{score_type}_by_model.png")
            plot_per_metric_bars(df, metric, "approach", score_type,
                                 per_dir / f"{safe}_{score_type}_by_approach.png")
            if n_models > 1:
                plot_per_metric_facets(df, metric, "model", "approach", score_type,
                                       per_dir / f"{safe}_{score_type}_approaches_per_model.png")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--eval-dir", required=True, type=Path,
                        help="Folder containing eval_*.json files.")
    parser.add_argument("--questions", required=True, type=Path,
                        help="classified_questions.json")
    parser.add_argument("--costs", type=Path, default=None,
                        help="Optional costs.json (see header for format).")
    parser.add_argument("--output-dir", type=Path, default=Path("./analysis_output"),
                        help="Where to save figures.")
    args = parser.parse_args()

    # Load
    evals = load_eval_files(args.eval_dir)
    print(f"Loaded {len(evals)} eval file(s).")
    classified_by_id = load_classified_questions(args.questions)
    print(f"Loaded {len(classified_by_id)} classified questions.")
    costs_table = load_costs(args.costs)

    # Build
    df = build_long_dataframe(evals, classified_by_id)
    n_models = df["model"].nunique()
    n_approaches = df["approach"].nunique()
    print(f"Dataframe: {len(df)} rows, "
          f"{n_models} model(s), {n_approaches} approach(es), "
          f"{df['metric'].nunique()} metric(s).")
    if n_models == 1:
        warnings.warn("Only one model — model comparisons will be trivial.")
    if n_approaches == 1:
        warnings.warn("Only one approach — approach comparisons will be trivial.")

    # Output dirs
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Score-based plots
    make_all_plots(df, args.output_dir)

    # Cost plots
    cost_df: pd.DataFrame | None = None
    if costs_table:
        cost_df = compute_costs(evals, costs_table, args.eval_dir)
        cost_dir = args.output_dir / "cost"
        cost_dir.mkdir(parents=True, exist_ok=True)
        cost_df.to_csv(cost_dir / "cost_summary.csv", index=False)
        plot_cost_charts(cost_df, df, cost_dir)
    else:
        warnings.warn("No costs.json provided — cost charts skipped.")

    # Breakdowns from classified_questions
    breakdowns_dir = args.output_dir / "breakdowns"
    breakdowns_dir.mkdir(parents=True, exist_ok=True)
    for col in ("domain", "difficulty_bucket", "answer_type"):
        plot_breakdown(df, col, breakdowns_dir)

    # Written report
    generate_report(df, cost_df, args.output_dir)

    print(f"\nDone. Figures in: {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()