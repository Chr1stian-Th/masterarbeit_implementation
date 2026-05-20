# DataEvaluation

Post-processing layer that consumes the DeepEval result files from `ArtefactsAndResults` and
produces publication-ready charts, cost breakdowns, and a structured Markdown report for the
master's thesis.

## Contents

```
DataEvaluation/
├── analyze_evals.py      # Main analysis script
├── costs.json            # Token pricing table per model
├── requirements.txt      # Python dependencies
├── Data/                 # Input: merged eval + output JSON files (one set per model)
└── analysis_output/      # Output: figures and report
    ├── all_metrics/      # Aggregate bar and spider charts (by model / by approach)
    ├── per_metric/       # Per-metric bar charts and faceted comparisons
    ├── cost/             # Cost and token-usage charts + CSV summary
    ├── breakdowns/       # Score breakdowns by domain, difficulty, answer type
    └── report.md         # Auto-generated Markdown report with all numeric tables
```

## Quick Start

```bash
cd DataEvaluation
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

python analyze_evals.py \
    --eval-dir  Data/ \
    --questions ../ExtraScripts/questionclassification/classified_questions.json \
    --costs     costs.json \
    --output-dir analysis_output
```

All figures and `report.md` are written to `analysis_output/`.

## Input Files

### `Data/`

Contains two types of JSON files per model × approach combination:

| Pattern | Description |
|---|---|
| `eval_<approach>_<ts>.json` | Per-question metric scores from DeepEval |
| `<approach>_<ts>.json` | Raw RAG outputs (referenced for actual token counts) |

The eval files must include:
- `approach` — string identifier (`agentic_rag`, `crag`, `lightrag`)
- `model_config.generation_model` — model string used as the series label
- `source_file` — filename of the corresponding raw output (for token lookup)
- `per_question` — list of `{question_id, metrics: {metric: {score, passed, errored?}}}`

### `costs.json`

Defines per-model pricing used to compute USD cost and score-per-dollar efficiency:

```json
{
    "google/gemini-3-flash-preview": { "input_per_1m": 0.50, "output_per_1m": 3.00 },
    "mistralai/mistral-small-2603":  { "input_per_1m": 0.15, "output_per_1m": 0.60 },
    "mistralai/mistral-large-2512":  { "input_per_1m": 0.50, "output_per_1m": 1.50 }
}
```

Token counts are read from the raw output files. If usage data is absent the script
falls back to a character-based estimate (4 chars/token + fixed overhead).

### `classified_questions.json` (external, from `ExtraScripts`)

Used for the breakdown plots. Each entry must contain:
```json
{ "id": "q001", "domain": "data_subject_rights", "difficulty": 0.4,
  "answer_type": "definitional", "ai_act_relevant": false }
```

## Outputs

### Score figures (`all_metrics/`, `per_metric/`)

For both `avg_score` and `pass_rate`:

| File | Description |
|---|---|
| `avg_score_by_model.png` | All metrics × model bar chart |
| `avg_score_by_approach.png` | All metrics × approach bar chart |
| `avg_score_approaches_per_model.png` | Faceted: one subplot per model, bars = approaches |
| `avg_score_models_per_approach.png` | Faceted: one subplot per approach, bars = models |
| `avg_score_spider_by_model.png` | Radar chart by model |
| `avg_score_spider_by_approach.png` | Radar chart by approach |
| `<metric>_avg_score_by_model.png` | Single-metric bar chart per model |
| `<metric>_avg_score_by_approach.png` | Single-metric bar chart per approach |
| `<metric>_avg_score_approaches_per_model.png` | Faceted single-metric chart |

All bar charts include 95 % confidence intervals.

### Cost figures (`cost/`)

| File | Description |
|---|---|
| `raw_cost_by_model_approach.png` | USD cost per model × approach |
| `raw_cost_by_model.png` | USD cost summed per model |
| `raw_cost_by_approach.png` | USD cost summed per approach |
| `score_per_usd_overall.png` | Average score / USD overall |
| `score_per_usd_per_metric.png` | Score / USD broken down per metric |
| `token_usage.png` | Stacked input + output token counts |
| `cost_summary.csv` | Tabular cost data |

### Breakdown figures (`breakdowns/`)

Grid of per-metric bar charts broken down by:
- `domain` — GDPR thematic domain (from `classified_questions.json`)
- `difficulty` — four buckets: easy / medium / hard / very hard
- `answer_type` — definitional / procedural / enumerative / comparative / application / multi_hop

### `report.md`

Markdown document with all numeric tables backing the figures:
- Dataset overview (models, approaches, metrics, question counts)
- Score summaries by model, by approach, by model × approach
- Per-metric results tables
- Cost analysis table with score-per-dollar
- Breakdown tables per domain / difficulty / answer type

## Dependencies

| Package | Version |
|---|---|
| pandas | 3.0.2 |
| matplotlib | 3.10.9 |
| numpy | 2.4.4 |
| scipy | 1.17.1 |

Python 3.10+ required.
