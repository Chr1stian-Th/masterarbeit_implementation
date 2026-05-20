# ExtraScripts

Standalone utility scripts that support the main evaluation pipeline but are not part
of the core RAG framework in `rag_evaluation/`.

## Contents

```
ExtraScripts/
├── requirements.txt                    # Top-level convenience requirements file
├── questionclassification/             # LLM-based question classifier
│   ├── classify_questions.py           # Main classifier script
│   ├── classified_questions.json       # Pre-generated output (committed for reproducibility)
│   ├── requirements.txt
│   ├── .env.example
│   └── .env                            # [gitignored] your API key
└── venv/                               # [gitignored]
```

## `questionclassification/`

Classifies every question in the GDPR/AI Act corpus along three dimensions — difficulty,
answer type, and thematic domain — using three LLM agents running in parallel per question.
The resulting `classified_questions.json` is consumed by `DataEvaluation/analyze_evals.py`
to produce the breakdown plots (by domain, difficulty, answer type).

### How it works

For each question the script fires three independent async API calls (via OpenRouter) in
parallel:

| Agent | Output fields |
|---|---|
| Difficulty | `difficulty` (0.0–1.0), `difficulty_rationale` |
| Answer type | `answer_type` (definitional / procedural / enumerative / comparative / application / multi_hop), `answer_type_rationale` |
| Domain | `domain`, `gdpr_articles` (up to 5), `ai_act_relevant`, `domain_rationale` |

All LLM outputs are validated with Pydantic before being merged into a single
`ClassifiedQuestion` object. Failures per dimension are recorded in an `errors` map
so partial results are never silently lost.

### Setup

```bash
cd ExtraScripts/questionclassification
python -m venv ../venv && source ../venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # add your OPENROUTER_API_KEY
```

### Usage

```bash
# Classify the active question corpus
python classify_questions.py ../../rag_evaluation/data/questions/questions.json \
    --output classified_questions.json

# Use a different model (default: openai/gpt-4o-mini)
python classify_questions.py questions.json \
    --model anthropic/claude-3-5-haiku \
    --output classified_questions.json
```

Progress and token usage are printed to stdout. Partial results (questions where one agent
failed) are still written to the output file with an `errors` field indicating which
dimension failed.

### Output Schema

```json
[
  {
    "id": "q001",
    "question": "What is the right to erasure under GDPR?",
    "difficulty": 0.35,
    "difficulty_rationale": "Answered by a direct quote from Art. 17.",
    "answer_type": "definitional",
    "answer_type_rationale": "Defines a specific right granted by the regulation.",
    "gdpr_articles": ["Art. 17"],
    "ai_act_relevant": false,
    "domain": "data_subject_rights",
    "domain_rationale": "Concerns rights of data subjects under Arts. 12-23."
  }
]
```

### Difficulty Scale

| Range | Label | Description |
|---|---|---|
| 0.00–0.25 | Basic | Single concept, direct quote from one article |
| 0.26–0.50 | Intermediate | Requires understanding 2–3 concepts |
| 0.51–0.75 | Advanced | Synthesising multiple articles or edge cases |
| 0.76–1.00 | Expert | Ambiguous interpretations, GDPR × AI Act interplay |

### Domain Categories

`principles_and_lawfulness` · `data_subject_rights` · `controller_processor_obligations` ·
`transfers` · `supervisory_authorities` · `enforcement_and_remedies` · `ai_act` · `cross_cutting`

### Dependencies

| Package | Version |
|---|---|
| aiohttp | 3.13.5 |
| pydantic | 2.13.3 |
| python-dotenv | 1.2.2 |

### Environment Variables

| Variable | Description |
|---|---|
| `OPENROUTER_API_KEY` | OpenRouter API key (required) |
