# Master's Thesis — Comparative Evaluation of RAG Approaches for regulatory question answering

Empirical evaluation of three Retrieval-Augmented Generation (RAG) architectures on a
GDPR / EU AI Act question-answering corpus.
Three commercial LLMs are compared across seven metrics covering answer quality, retrieval
quality, legal interpretability, and cost efficiency.

## Repository Layout

```
masterarbeit_implementation/
├── rag_evaluation/          # Core RAG framework: ingestion, approaches, evaluation
├── ArtefactsAndResults/     # Archived outputs and evaluation results for every run
├── DataEvaluation/          # Statistical analysis, visualisation, and report generation
└── ExtraScripts/            # Standalone utilities (question classifier)
```

---

## `rag_evaluation/` — Core RAG Framework

The primary codebase. An orchestrated pipeline that ingests source PDFs, runs three RAG
approaches, and evaluates their answers with DeepEval / RAGAS metrics.

### RAG Approaches

| Approach | Key idea |
|---|---|
| **LightRAG** | Knowledge-graph + vector hybrid retrieval ([HKUDS/LightRAG](https://github.com/HKUDS/LightRAG)) |
| **Agentic RAG** | Query classification (no-retrieval / single-step / multi-step) → adaptive retrieval → hallucination check |
| **CRAG** | Corrective RAG: retrieve → grade documents (Correct / Incorrect / Ambiguous) → refine query if needed → generate |

### Evaluation Metrics

| Metric | File |
|---|---|
| Faithfulness | `evaluation/metrics/faithfulness.py` |
| Answer Relevancy | `evaluation/metrics/answer_relevancy.py` |
| Context Precision | `evaluation/metrics/context_precision.py` |
| Context Recall | `evaluation/metrics/context_recall.py` |
| Context Relevancy | `evaluation/metrics/context_relevancy.py` |
| Legal Interpretability | `evaluation/metrics/legal_interpretability.py` |
| Regulatory Grounding | `evaluation/metrics/regulatory_grounding.py` |

### Quick Start

```bash
cd rag_evaluation

# 1. Copy and fill in API keys for each component
cp ingestion/.env.example            ingestion/.env
cp approaches/lightrag_approach/.env.example approaches/lightrag_approach/.env
cp approaches/agentic_rag/.env.example       approaches/agentic_rag/.env
cp approaches/crag/.env.example              approaches/crag/.env
cp evaluation/.env.example                   evaluation/.env

# 2. Place source PDFs in data/gdpr/
#    Place question corpus in data/questions/questions.json

# 3. Run the full pipeline end-to-end
chmod +x orchestrator.sh setup_envs.sh
./orchestrator.sh
```

Individual stages:
```bash
./orchestrator.sh --setup          # Create virtual environments only
./orchestrator.sh --ingest         # Ingest PDFs into ChromaDB and LightRAG
./orchestrator.sh --run lightrag   # Run a single approach
./orchestrator.sh --evaluate       # Evaluate all outputs in outputs/
```

See [rag_evaluation/README.md](rag_evaluation/README.md) for full documentation including
configuration options, output format, and how to add new metrics.

---

## `ExtraScripts/` — Question Classifier

Utility that enriches the question corpus with metadata (difficulty, answer type, GDPR
domain) needed for the breakdown analysis. Runs three LLM agents per question in parallel
via OpenRouter.

```bash
cd ExtraScripts/questionclassification
pip install -r requirements.txt
cp .env.example .env   # add OPENROUTER_API_KEY

python classify_questions.py \
    ../../rag_evaluation/data/questions/questions.json \
    --output classified_questions.json
```

The committed `classified_questions.json` is the pre-generated output used for all thesis
experiments. Re-run only if the question corpus changes.

See [ExtraScripts/README.md](ExtraScripts/README.md) for full documentation.

---

## `ArtefactsAndResults/` — Experimental Artefacts

Archived snapshots of all pipeline runs, kept for reproducibility.

| Sub-folder | Description |
|---|---|
| `first_test_run/` | Initial smoke test (March 2026), includes DB snapshots |
| `second_test_run_19_04/` | Second preliminary run (April 19 2026) |
| `results_mistral-small-2603/` | Main experiment — Mistral Small 2603 |
| `results_mistral-large-3/` | Main experiment — Mistral Large 2512 |
| `results_gemini-flash-3/` | Main experiment — Gemini Flash 3 |

Each folder contains raw approach outputs (`outputs/`), DeepEval evaluation results
(`results/`), retry artefacts (`retry/`), and pipeline logs.

The `merged_eval_*.json` files in `results/` are the inputs consumed by `DataEvaluation`.

See [ArtefactsAndResults/README.md](ArtefactsAndResults/README.md) for full documentation.

---

## `DataEvaluation/` — Analysis and Visualisation

Post-processing script that turns eval JSON files into charts and a Markdown report.

```bash
cd DataEvaluation
pip install -r requirements.txt

python analyze_evals.py \
    --eval-dir  Data/ \
    --questions ../ExtraScripts/questionclassification/classified_questions.json \
    --costs     costs.json \
    --output-dir analysis_output
```

Generated outputs in `analysis_output/`:

| Sub-folder | Contents |
|---|---|
| `all_metrics/` | Aggregate bar and spider charts (by model, by approach) |
| `per_metric/` | One chart set per metric |
| `cost/` | USD cost charts, score-per-dollar charts, `cost_summary.csv` |
| `breakdowns/` | Score grids by domain / difficulty / answer type |
| `report.md` | Full numeric Markdown report |

See [DataEvaluation/README.md](DataEvaluation/README.md) for full documentation.

---

## End-to-End Workflow

```
1. Prepare corpus
   └─ Place PDFs in rag_evaluation/data/gdpr/
   └─ Place questions in rag_evaluation/data/questions/questions.json

2. Classify questions  (ExtraScripts)
   └─ python classify_questions.py questions.json --output classified_questions.json

3. Run evaluation pipeline  (rag_evaluation)
   └─ ./orchestrator.sh
   └─ Results land in rag_evaluation/outputs/ and rag_evaluation/results/

4. Archive results  (ArtefactsAndResults)
   └─ Copy outputs/ and results/ into a new sub-folder

5. Copy merged_eval_*.json and output *.json into DataEvaluation/Data/

6. Analyse  (DataEvaluation)
   └─ python analyze_evals.py --eval-dir Data/ --questions classified_questions.json
                               --costs costs.json --output-dir analysis_output
```

## Models Evaluated

| Model | Provider | Use |
|---|---|---|
| `mistralai/mistral-small-2603` | Mistral AI | Generation + classification |
| `mistralai/mistral-large-2512` | Mistral AI | Generation + classification |
| `google/gemini-3-flash-preview` | Google | Generation + classification |

Embeddings: `text-embedding-3-large` (OpenAI) for all runs.
Evaluation judge: configured separately in `evaluation/.env`.

## Requirements

- Python 3.10+ (3.11 recommended)
- OpenRouter API key (generation, evaluation, etc...)
- ~10 GB disk for ChromaDB + LightRAG storage + virtual environments
