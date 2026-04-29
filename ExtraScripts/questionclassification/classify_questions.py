"""
GDPR Question Classifier
========================
Classifies questions into: difficulty (0-1), answer type, and GDPR domain.
Runs 3 agents per question in parallel using OpenRouter's API.
LLM outputs and input JSON are validated with Pydantic.

Setup:
    pip install aiohttp pydantic python-dotenv

Usage:
    export OPENROUTER_API_KEY=sk-or-...
    python classify_questions.py questions.json

    # or with a .env file containing OPENROUTER_API_KEY=sk-or-...
    python classify_questions.py questions.json

    # optionally specify a model and output file:
    python classify_questions.py questions.json --model anthropic/claude-3-5-haiku --output results.json
"""

import argparse
import asyncio
import json
import os
import sys
import time
from enum import Enum
from pathlib import Path
from typing import Annotated

try:
    import aiohttp
except ImportError:
    sys.exit("Missing dependency: run  pip install aiohttp pydantic")

try:
    from pydantic import BaseModel, Field, ValidationError, field_validator
except ImportError:
    sys.exit("Missing dependency: run  pip install pydantic")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv is optional; key can come from the shell environment


# ── Input schema ──────────────────────────────────────────────────────────────

class Question(BaseModel):
    id: str
    question: str
    ground_truth: str

    # Coerce int/float ids (e.g. accidental {"id": 1}) to string
    @field_validator("id", mode="before")
    @classmethod
    def coerce_id(cls, v: object) -> str:
        return str(v)


# ── Agent output schemas ──────────────────────────────────────────────────────

class AnswerType(str, Enum):
    definitional = "definitional"
    procedural   = "procedural"
    enumerative  = "enumerative"
    comparative  = "comparative"
    application  = "application"
    multi_hop    = "multi_hop"


class Domain(str, Enum):
    principles_and_lawfulness        = "principles_and_lawfulness"
    data_subject_rights              = "data_subject_rights"
    controller_processor_obligations = "controller_processor_obligations"
    transfers                        = "transfers"
    supervisory_authorities          = "supervisory_authorities"
    enforcement_and_remedies         = "enforcement_and_remedies"
    ai_act                           = "ai_act"
    cross_cutting                    = "cross_cutting"


class DifficultyResult(BaseModel):
    id: str
    difficulty: Annotated[float, Field(ge=0.0, le=1.0)]
    difficulty_rationale: str

    # Some models return difficulty as a quoted string e.g. "0.7"
    @field_validator("difficulty", mode="before")
    @classmethod
    def coerce_difficulty(cls, v: object) -> float:
        return float(v)


class TypeResult(BaseModel):
    id: str
    answer_type: AnswerType
    answer_type_rationale: str


class DomainResult(BaseModel):
    id: str
    gdpr_articles: list[str] = Field(max_length=5)
    ai_act_relevant: bool
    domain: Domain
    domain_rationale: str


# ── Merged output schema ──────────────────────────────────────────────────────

class ClassifiedQuestion(BaseModel):
    id: str
    question: str
    difficulty: float | None                = None
    difficulty_rationale: str | None        = None
    answer_type: AnswerType | None          = None
    answer_type_rationale: str | None       = None
    gdpr_articles: list[str]               = Field(default_factory=list)
    ai_act_relevant: bool | None           = None
    domain: Domain | None                  = None
    domain_rationale: str | None           = None
    errors: dict[str, str]                 = Field(default_factory=dict)


# ── Token usage ───────────────────────────────────────────────────────────────

class TokenUsage(BaseModel):
    prompt_tokens: int     = 0
    completion_tokens: int = 0
    total_tokens: int      = 0
    calls: int             = 0

    def add(self, other: "TokenUsage") -> None:
        self.prompt_tokens     += other.prompt_tokens
        self.completion_tokens += other.completion_tokens
        self.total_tokens      += other.total_tokens
        self.calls             += other.calls

    @classmethod
    def from_response(cls, resp: dict) -> "TokenUsage":
        u = resp.get("usage", {})
        return cls(
            prompt_tokens     = u.get("prompt_tokens", 0),
            completion_tokens = u.get("completion_tokens", 0),
            total_tokens      = u.get("total_tokens", 0),
            calls             = 1,
        )


# ── Prompts ──────────────────────────────────────────────────────────────────

DIFFICULTY_SYSTEM = """You are a legal Q&A difficulty classifier specialising in EU data protection law (GDPR) and the EU AI Act.

Given a question and its ground-truth answer, assign a difficulty score between 0.0 and 1.0:
  0.0-0.25  Basic        - Single concept, answered by a direct quote from one article.
  0.26-0.50 Intermediate - Requires understanding 2-3 concepts or applying a principle.
  0.51-0.75 Advanced     - Requires synthesising multiple articles or reasoning about edge cases.
  0.76-1.0  Expert       - Ambiguous interpretations, interplay between GDPR and other regulations.

Respond ONLY with valid JSON, no markdown fences, no preamble:
{"id":"<id>","difficulty":<float 0.0-1.0>,"difficulty_rationale":"<1-2 sentences>"}"""

TYPE_SYSTEM = """You are a legal Q&A taxonomy classifier for GDPR and the EU AI Act.

Classify the answer type into exactly one of:
  definitional  - defines a concept, term, or right
  procedural    - describes steps, obligations, or a process
  enumerative   - is a list of items without requiring inference
  comparative   - contrasts two or more concepts or roles
  application   - applies a rule to a scenario or example
  multi_hop     - requires chaining logic across multiple articles

Respond ONLY with valid JSON, no markdown fences, no preamble:
{"id":"<id>","answer_type":"<category>","answer_type_rationale":"<1 sentence>"}"""

DOMAIN_SYSTEM = """You are a legal domain tagger for GDPR and the EU AI Act.

Identify:
1. Primary GDPR articles (up to 5, ordered by relevance)
2. Whether the EU AI Act is relevant (true/false)
3. Thematic domain - pick exactly one from:
     principles_and_lawfulness        (Arts. 5-11)
     data_subject_rights              (Arts. 12-23)
     controller_processor_obligations (Arts. 24-43)
     transfers                        (Arts. 44-49)
     supervisory_authorities          (Arts. 51-59)
     enforcement_and_remedies         (Arts. 77-84)
     ai_act                           (EU AI Act primary)
     cross_cutting                    (spans multiple domains)

Respond ONLY with valid JSON, no markdown fences, no preamble:
{"id":"<id>","gdpr_articles":["Art. X"],"ai_act_relevant":<bool>,"domain":"<domain>","domain_rationale":"<1 sentence>"}"""


# ── OpenRouter call ───────────────────────────────────────────────────────────

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

async def call_openrouter(
    session: aiohttp.ClientSession,
    api_key: str,
    model: str,
    system_prompt: str,
    user_content: str,
) -> dict:
    payload = {
        "model": model,
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_content},
        ],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://claude.ai",
        "X-Title": "GDPR Q Classifier",
    }
    async with session.post(OPENROUTER_URL, json=payload, headers=headers) as resp:
        if resp.status != 200:
            body = await resp.text()
            raise RuntimeError(f"OpenRouter {resp.status}: {body}")
        return await resp.json()


def extract_json_text(raw: str) -> str:
    """Strip markdown fences that some models add despite instructions."""
    return raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()


# ── Per-question pipeline ─────────────────────────────────────────────────────

async def classify_question(
    session: aiohttp.ClientSession,
    api_key: str,
    model: str,
    question: Question,
) -> tuple[ClassifiedQuestion, TokenUsage]:
    user_content = (
        f"ID: {question.id}\n"
        f"Question: {question.question}\n"
        f"Answer: {question.ground_truth}"
    )

    diff_task   = call_openrouter(session, api_key, model, DIFFICULTY_SYSTEM, user_content)
    type_task   = call_openrouter(session, api_key, model, TYPE_SYSTEM,       user_content)
    domain_task = call_openrouter(session, api_key, model, DOMAIN_SYSTEM,     user_content)

    responses = await asyncio.gather(diff_task, type_task, domain_task, return_exceptions=True)

    result = ClassifiedQuestion(id=question.id, question=question.question)
    total  = TokenUsage()

    diff_resp, type_resp, domain_resp = responses

    # Difficulty agent
    if isinstance(diff_resp, Exception):
        result.errors["difficulty"] = str(diff_resp)
        print(f"  [!] difficulty agent failed for {question.id}: {diff_resp}", file=sys.stderr)
    else:
        total.add(TokenUsage.from_response(diff_resp))
        try:
            parsed = DifficultyResult.model_validate_json(
                extract_json_text(diff_resp["choices"][0]["message"]["content"])
            )
            result.difficulty           = parsed.difficulty
            result.difficulty_rationale = parsed.difficulty_rationale
        except (ValidationError, Exception) as e:
            result.errors["difficulty"] = str(e)
            print(f"  [!] difficulty parse error ({question.id}): {e}", file=sys.stderr)

    # Answer type agent
    if isinstance(type_resp, Exception):
        result.errors["answer_type"] = str(type_resp)
        print(f"  [!] answer_type agent failed for {question.id}: {type_resp}", file=sys.stderr)
    else:
        total.add(TokenUsage.from_response(type_resp))
        try:
            parsed = TypeResult.model_validate_json(
                extract_json_text(type_resp["choices"][0]["message"]["content"])
            )
            result.answer_type           = parsed.answer_type
            result.answer_type_rationale = parsed.answer_type_rationale
        except (ValidationError, Exception) as e:
            result.errors["answer_type"] = str(e)
            print(f"  [!] answer_type parse error ({question.id}): {e}", file=sys.stderr)

    # Domain agent
    if isinstance(domain_resp, Exception):
        result.errors["domain"] = str(domain_resp)
        print(f"  [!] domain agent failed for {question.id}: {domain_resp}", file=sys.stderr)
    else:
        total.add(TokenUsage.from_response(domain_resp))
        try:
            parsed = DomainResult.model_validate_json(
                extract_json_text(domain_resp["choices"][0]["message"]["content"])
            )
            result.gdpr_articles    = parsed.gdpr_articles
            result.ai_act_relevant  = parsed.ai_act_relevant
            result.domain           = parsed.domain
            result.domain_rationale = parsed.domain_rationale
        except (ValidationError, Exception) as e:
            result.errors["domain"] = str(e)
            print(f"  [!] domain parse error ({question.id}): {e}", file=sys.stderr)

    return result, total


# ── Main ──────────────────────────────────────────────────────────────────────

async def main(input_path: str, model: str, output_path: str | None) -> None:
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        sys.exit(
            "Error: OPENROUTER_API_KEY is not set.\n"
            "  export OPENROUTER_API_KEY=sk-or-...\n"
            "  or add it to a .env file in the same directory."
        )

    # Load and validate input
    try:
        raw = json.loads(Path(input_path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        sys.exit(f"Error: file not found - {input_path}")
    except json.JSONDecodeError as e:
        sys.exit(f"Error: invalid JSON in {input_path} - {e}")

    if not isinstance(raw, list) or not raw:
        sys.exit("Error: JSON file must contain a non-empty array of question objects.")

    questions: list[Question] = []
    for i, item in enumerate(raw):
        try:
            questions.append(Question.model_validate(item))
        except ValidationError as e:
            sys.exit(f"Error: question at index {i} failed validation:\n{e}")

    print(f"\nGDPR Question Classifier")
    print(f"  Model : {model}")
    print(f"  Input : {input_path}  ({len(questions)} question{'s' if len(questions) != 1 else ''})")
    print(f"  Output: {output_path or 'stdout'}\n")

    all_results: list[ClassifiedQuestion] = []
    grand_total = TokenUsage()
    t0 = time.perf_counter()

    connector = aiohttp.TCPConnector(limit=10)
    async with aiohttp.ClientSession(connector=connector) as session:
        for i, q in enumerate(questions, 1):
            print(f"[{i}/{len(questions)}] {q.id} - {q.question[:70]}...")
            result, usage = await classify_question(session, api_key, model, q)
            all_results.append(result)
            grand_total.add(usage)

            # Live preview
            if result.difficulty is not None:
                bar = "X" * int(result.difficulty * 20) + "." * (20 - int(result.difficulty * 20))
                print(f"         difficulty : {result.difficulty:.2f}  [{bar}]")
            print(f"         answer type : {result.answer_type.value if result.answer_type else '-'}")
            print(f"         domain      : {result.domain.value if result.domain else '-'}")
            arts = ", ".join(result.gdpr_articles) or "-"
            print(f"         articles    : {arts}")
            if result.errors:
                print(f"         errors      : {list(result.errors.keys())}")
            print()

    elapsed = time.perf_counter() - t0

    # Token summary
    print("-" * 50)
    print(f"Token usage")
    print(f"  Prompt      : {grand_total.prompt_tokens:>8,}")
    print(f"  Completion  : {grand_total.completion_tokens:>8,}")
    print(f"  Total       : {grand_total.total_tokens:>8,}")
    print(f"  API calls   : {grand_total.calls:>8}")
    print(f"  Elapsed     : {elapsed:.1f}s")
    print("-" * 50)

    # Serialise - exclude null fields and empty errors for cleaner output
    output_data = [
        r.model_dump(exclude_none=True, exclude={"errors"} if not r.errors else set())
        for r in all_results
    ]
    output = json.dumps(output_data, indent=2, ensure_ascii=False)

    if output_path:
        Path(output_path).write_text(output, encoding="utf-8")
        print(f"\nResults saved to {output_path}")
    else:
        print("\nResults:\n")
        print(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Classify GDPR Q&A questions using a 3-agent OpenRouter pipeline."
    )
    parser.add_argument("input", help="Path to input JSON file")
    parser.add_argument(
        "--model", default="openai/gpt-4o-mini",
        help="OpenRouter model string (default: openai/gpt-4o-mini)"
    )
    parser.add_argument(
        "--output", default=None,
        help="Path to write output JSON (default: print to stdout)"
    )
    args = parser.parse_args()
    asyncio.run(main(args.input, args.model, args.output))