# ArtefactsAndResults

Archived snapshots of every experimental run produced during the master's thesis evaluation.
Each sub-folder represents one complete pipeline execution (ingestion → RAG approach runs → DeepEval evaluation).

## Folder Overview

```
ArtefactsAndResults/
├── first_test_run/            # Initial full-stack smoke test (March 2026)
├── second_test_run_19_04/     # Second preliminary run (April 19 2026)
├── results_mistral-small-2603/ # Main experiment – Mistral Small 2603
├── results_mistral-large-3/   # Main experiment – Mistral Large 2512
└── results_gemini-flash-3/    # Main experiment – Gemini Flash 3
```

## Sub-folder Contents

Each experiment folder follows the same layout (differences noted below):

```
<experiment>/
├── outputs/                   # Raw JSON answers produced by each RAG approach
│   ├── <approach>_<timestamp>.json              # Full output per approach
│   ├── errors_manifest_<approach>_<ts>.json     # Questions that failed / errored
│   └── retry_<approach>_<ts>.json               # Re-run of failed questions
├── results/                   # DeepEval evaluation results
│   ├── eval_<approach>_<ts>.json                # Raw per-question metric scores
│   ├── merged_eval_<approach>_<ts>.json         # Outputs merged into eval file
│   └── token_usage_evaluation_<ts>.json         # Token cost of the evaluation LLM calls
├── retry/                     # Evaluation of the retry outputs
│   ├── retry_eval_<approach>_<ts>.json
│   └── token_usage_retry_<ts>.json
└── pipeline_<timestamp>.log   # Orchestrator log for the run
```

### first_test_run (additional content)

In addition to the standard layout the first test run also archives the ingested databases:

```
first_test_run/
├── chromadb/   # ChromaDB vector store snapshot (HNSW index + SQLite)
├── lightrag/   # LightRAG graph storage (GraphML + key-value JSON stores)
├── outputs/
└── results/
    └── summary_<ts>.json   # Aggregated metric summary across all approaches
```

### results_mistral-large-3 (additional content)

```
results_mistral-large-3/
└── errors_lightrag/   # Intermediate LightRAG output files saved during debugging
```

## Output File Schema

**`outputs/<approach>_<ts>.json`** — raw approach output:
```json
{
  "approach": "agentic_rag",
  "timestamp": "2026-04-20T11:43:32",
  "model_config": { "generation_model": "...", "embedding_model": "..." },
  "results": [
    {
      "question_id": "q001",
      "input": "...",
      "retriever_context": ["..."],
      "output": "...",
      "ground_truth": "...",
      "token_usage": { "prompt_tokens": 850, "completion_tokens": 200, "total_tokens": 1050 },
      "latency_seconds": 2.3
    }
  ]
}
```

**`results/merged_eval_<approach>_<ts>.json`** — evaluation results (used by `DataEvaluation`):
```json
{
  "approach": "agentic_rag",
  "source_file": "agentic_rag_2026-04-20T11:43:32.json",
  "model_config": { "generation_model": "...", ... },
  "metrics": {
    "answer_relevancy": { "average_score": 0.78, "pass_rate": 0.71, "total_cases": 153, ... }
  },
  "per_question": [
    {
      "question_id": "q001",
      "metrics": { "answer_relevancy": { "score": 0.82, "passed": true } }
    }
  ]
}
```

## Models Tested

| Folder | Model ID |
|---|---|
| `results_mistral-small-2603` | `mistralai/mistral-small-2603` |
| `results_mistral-large-3` | `mistralai/mistral-large-2512` |
| `results_gemini-flash-3` | `google/gemini-3-flash-preview` |

## RAG Approaches Covered

All three experiment folders contain results for:
- **agentic_rag** — multi-stage adaptive retrieval with query classification and hallucination checking
- **crag** — Corrective RAG with document grading and query refinement
- **lightrag** — graph-based hybrid retrieval using LightRAG

## Relationship to Other Folders

- The `merged_eval_*.json` files in `results/` are copied into `DataEvaluation/Data/` for statistical analysis.
- The `outputs/*.json` files are referenced by the eval files via the `source_file` field so `analyze_evals.py` can look up actual token counts.
