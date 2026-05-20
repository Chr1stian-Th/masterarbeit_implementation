# RAG Evaluation Framework

A comprehensive framework for evaluating Retrieval-Augmented Generation (RAG) approaches
against a GDPR/AI Act question-answering corpus using [DeepEval](https://github.com/confident-ai/deepeval) and based on RAGAS.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        orchestrator.sh                          │
│  Sets up venvs, runs ingestion, executes approaches, evaluates │
└──────────┬──────────────┬──────────────┬──────────────┬─────────┘
           │              │              │              │
     ┌─────▼─────┐ ┌─────▼─────┐ ┌─────▼─────┐ ┌─────▼──────┐
     │ Ingestion │ │ LightRAG  │ │ Agentic   │ │   CRAG     │
     │ Pipeline  │ │ (graph)   │ │ RAG       │ │(corrective)│
     └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └─────┬──────┘
           │              │              │              │
     ┌─────▼─────┐       │        ┌─────▼─────┐       │
     │ ChromaDB  │       │        │ ChromaDB  │       │
     │ + LightRAG│       │        │ (shared)  ├───────┘
     └───────────┘       │        └───────────┘
                   ┌─────▼─────┐
                   │ LightRAG  │
                   │ Graph DB  │
                   └───────────┘
           │              │              │              │
           └──────────────┴──────┬───────┴──────────────┘
                                 │ outputs/*.json
                           ┌─────▼─────┐
                           │ DeepEval  │
                           │ Evaluator │
                           └─────┬─────┘
                                 │ results/
                                 ▼
                         Evaluation Reports
```

## RAG Approaches

### 1. LightRAG (Graph-Based RAG)
Uses [HKUDS/LightRAG](https://github.com/HKUDS/LightRAG) which builds a knowledge graph
from the GDPR corpus and performs hybrid (graph + vector) retrieval.

### 2. Agentic RAG (Adaptive Retrieval)
A multi-stage pipeline:
- **Query Classifier**: Categorizes questions as no-retrieval / single-step / multi-step
- **Dynamic Retrieval**: Adapts retrieval strategy based on classification
- **Hallucination Check**: Verifies answer is grounded in retrieved context

### 3. CRAG (Corrective RAG)
Implements the Corrective Retrieval-Augmented Generation pattern:
- **Retrieve** documents from ChromaDB
- **Grade** each document for relevance (Correct / Incorrect / Ambiguous)
- **Refine** by re-retrieving with improved queries if confidence is low
- **Generate** with refined, high-quality context

## Project Structure

```
masterarbeit_implementation/
└── rag_evaluation/
    ├── README.md
    ├── orchestrator.sh              # Main entry: runs everything end-to-end
    ├── setup_envs.sh                # Creates virtual environments
    ├── .gitignore
    ├── config/
    │   └── settings.yaml            # Global configuration
    ├── data/
    │   ├── README.md
    │   ├── gdpr/                    # GDPR and AI Act source PDFs
    │   │   ├── GDPR_EN.pdf
    │   │   └── AI_ACT_EN.pdf
    │   └── questions/
    │       ├── questions.json       # Active question corpus (with ground truth)
    │       └── allquestions.json    # Full question pool
    ├── db/
    │   ├── chromadb/                # [gitignored] Shared ChromaDB vector store
    │   └── lightrag/                # [gitignored] LightRAG graph storage
    ├── .venvs/                      # [gitignored] Per-approach virtual environments
    │   ├── ingestion/
    │   ├── lightrag/
    │   ├── agentic_rag/
    │   ├── crag/
    │   └── evaluation/
    ├── .deepeval/                   # [gitignored] DeepEval telemetry cache
    ├── approaches/
    │   ├── common/                  # Shared utilities (imported via sys.path)
    │   │   ├── __init__.py
    │   │   ├── config_loader.py     # Loads settings.yaml
    │   │   ├── schemas.py           # Output data models
    │   │   ├── token_tracker.py     # OpenAI token usage tracking
    │   │   └── output_logger.py     # Standardized result logging
    │   ├── lightrag_approach/
    │   │   ├── requirements.txt
    │   │   ├── .env.example
    │   │   └── run.py
    │   ├── agentic_rag/
    │   │   ├── requirements.txt
    │   │   ├── .env.example
    │   │   └── run.py
    │   └── crag/
    │       ├── requirements.txt
    │       ├── .env.example
    │       └── run.py
    ├── ingestion/
    │   ├── requirements.txt
    │   ├── .env.example
    │   ├── pdf_utils.py             # PDF parsing helpers
    │   ├── ingest_chromadb.py       # Ingest corpus into ChromaDB
    │   └── ingest_lightrag.py       # Ingest corpus into LightRAG
    ├── evaluation/
    │   ├── requirements.txt
    │   ├── .env.example
    │   ├── evaluate.py              # Main evaluation entry point
    │   └── metrics/
    │       ├── __init__.py          # Metric registry
    │       ├── faithfulness.py
    │       ├── answer_relevancy.py
    │       ├── context_precision.py
    │       ├── context_recall.py
    │       ├── context_relevancy.py
    │       ├── legal_interpretability.py
    │       └── regulatory_grounding.py
    ├── outputs/                     # [gitignored] JSON results from approach runs
    └── results/                     # [gitignored] JSON evaluation reports
```

## Quick Start

### 1. Prepare Data
Place your source PDFs in `data/gdpr/` (e.g. `GDPR_EN.pdf`, `AI_ACT_EN.pdf`).
The ingestion pipeline uses `pdf_utils.py` to parse and chunk these automatically.

Place your question corpus in `data/questions/questions.json`:

```json
[
  {
    "id": "q001",
    "question": "What is the right to erasure under GDPR?",
    "ground_truth": "Article 17 establishes the right to erasure..."
  }
]
```

A full question pool is kept in `data/questions/allquestions.json`; copy a subset into `questions.json` to control which questions are evaluated.

### 2. Configure Environment
Copy `.env.example` files and fill in your API keys:

```bash
# Each approach can have its own API key
cp ingestion/.env.example ingestion/.env
cp approaches/lightrag_approach/.env.example approaches/lightrag_approach/.env
cp approaches/agentic_rag/.env.example approaches/agentic_rag/.env
cp approaches/crag/.env.example approaches/crag/.env
cp evaluation/.env.example evaluation/.env
```

### 3. Run Everything
```bash
chmod +x orchestrator.sh setup_envs.sh
./orchestrator.sh
```

Or run individual stages:
```bash
./orchestrator.sh --setup          # Create venvs only
./orchestrator.sh --ingest         # Ingest data only
./orchestrator.sh --run lightrag   # Run one approach
./orchestrator.sh --evaluate       # Evaluate outputs
```

## Configuration

Edit `config/settings.yaml` to adjust:
- Model names (generation + embedding)
- Chunk sizes for ingestion
- Retrieval parameters (top-k, similarity thresholds)
- Parallelization settings (max workers)
- Output paths

## Output Format

Each approach produces a JSON file in `outputs/`:

```json
{
  "approach": "agentic_rag",
  "timestamp": "2025-02-23T10:30:00",
  "model_config": { "generation_model": "gpt-4o-mini", "embedding_model": "text-embedding-3-small" },
  "results": [
    {
      "question_id": "q001",
      "input": "What is the right to erasure?",
      "retriever_context": ["Article 17 paragraph 1...", "Article 17 paragraph 2..."],
      "output": "The right to erasure, also known as...",
      "ground_truth": "Article 17 establishes...",
      "token_usage": { "prompt_tokens": 850, "completion_tokens": 200, "total_tokens": 1050 },
      "latency_seconds": 2.3,
      "metadata": {}
    }
  ],
  "total_token_usage": { "prompt_tokens": 8500, "completion_tokens": 2000, "total_tokens": 10500 }
}
```

## Evaluation

The evaluation framework uses DeepEval and is designed to be extensible:

```bash
# Evaluate all outputs with all registered metrics
python evaluation/evaluate.py --input-dir outputs/ --output-dir results/

# Evaluate a specific approach
python evaluation/evaluate.py --input-dir outputs/ --filter lightrag --output-dir results/
```

### Metrics

| Metric | File |
|---|---|
| Faithfulness | `faithfulness.py` |
| Answer Relevancy | `answer_relevancy.py` |
| Context Precision | `context_precision.py` |
| Context Recall | `context_recall.py` |
| Context Relevancy | `context_relevancy.py` |
| Legal Interpretability | `legal_interpretability.py` |
| Regulatory Grounding | `regulatory_grounding.py` |

To add new metrics, create a file in `evaluation/metrics/` following the existing patterns and register it in `__init__.py`.

## Requirements

- Python 3.10+ (3.11 recommended)
- OpenAI API key(s)
- ~10GB disk space for ChromaDB + LightRAG storage + all the necessary virtual environments
