#!/usr/bin/env python3
"""
Ingest GDPR text documents into LightRAG's graph-based storage.

Reads ``.txt`` and ``.md`` files from the configured GDPR data directory
and inserts them into LightRAG, which builds a knowledge graph with
entity extraction and relationship mapping.

LightRAG manages its own chunking and indexing internally.

Usage:
    python ingestion/ingest_lightrag.py

Environment Variables:
    OPENAI_API_KEY: Required. Your OpenAI API key.
    OPENAI_BASE_URL: Optional. Custom API base URL.
"""

import os
import sys
import glob
import asyncio
import json
from datetime import datetime, timezone
from functools import partial

from dotenv import load_dotenv

# Ensure ingestion/ is on path for pdf_utils
sys.path.insert(0, os.path.dirname(__file__))

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from approaches.common.config_loader import load_config

# Load environment variables from ingestion/.env
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))


async def ingest_async(config_path: str | None = None) -> None:
    """Run the LightRAG ingestion pipeline asynchronously.

    LightRAG's insert API is async, so this function handles the
    async lifecycle. Called by :func:`ingest` which wraps it in
    ``asyncio.run()``.

    Steps:
        1. Load GDPR text files.
        2. Initialize LightRAG with OpenAI models.
        3. Insert each document (LightRAG handles chunking and graph construction).

    Args:
        config_path: Optional path to ``settings.yaml``.
    """
    # Import LightRAG here so it's only needed in the lightrag venv
    import tiktoken
    from lightrag import LightRAG, QueryParam
    from lightrag.llm.openai import openai_complete_if_cache, openai_embed
    from lightrag.utils import EmbeddingFunc

    def _count_tokens(text: str, model: str) -> int:
        try:
            enc = tiktoken.encoding_for_model(model)
        except KeyError:
            enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))

    cfg = load_config(config_path)
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required.")

    # Set for LightRAG's internal OpenAI calls
    os.environ["OPENAI_API_KEY"] = api_key

    embedding_model = cfg["models"]["embedding_model"]
    embedding_dim = cfg["models"]["embedding_dimensions"]
    generation_model = cfg["models"]["generation_model"]
    working_dir = os.path.join(PROJECT_ROOT, cfg["lightrag"]["working_dir"])
    data_dir = os.path.join(PROJECT_ROOT, cfg["ingestion"]["gdpr_data_dir"])
    max_token_size = cfg["lightrag"]["max_token_size"]

    os.makedirs(working_dir, exist_ok=True)

    # --- Initialize LightRAG ---
    base_url = os.environ.get("OPENAI_BASE_URL")
    rag = LightRAG(
        working_dir=working_dir,
        llm_model_func=partial(openai_complete_if_cache, generation_model),
        llm_model_name=generation_model,
        llm_model_max_async=4,
        llm_model_kwargs={
            "base_url": base_url,
            "api_key": api_key,
        },
        embedding_func=EmbeddingFunc(
            embedding_dim=embedding_dim,
            max_token_size=max_token_size,
            func=lambda texts: openai_embed(
                texts,
                model=embedding_model,
                base_url=base_url,
                api_key=api_key,
            ),
        ),
        chunk_token_size=cfg["lightrag"].get("chunk_token_size", 1200),
        entity_extract_max_gleaning=cfg["lightrag"].get(
            "entity_extract_max_gleaning", 1
        ),
    )

    await rag.initialize_storages()

    # Import here so the ingestion directory is on sys.path (set above)
    from pdf_utils import pdf_to_markdown

    # --- Load and insert documents ---
    txt_files = sorted(
        glob.glob(os.path.join(data_dir, "*.txt"))
        + glob.glob(os.path.join(data_dir, "*.md"))
    )
    pdf_files = sorted(glob.glob(os.path.join(data_dir, "*.pdf")))
    all_files = txt_files + pdf_files

    if not all_files:
        print(f"[LightRAG Ingest] No .txt, .md, or .pdf files found in {data_dir}")
        print(f"[LightRAG Ingest] Please place GDPR document files in {data_dir}")
        return

    print(
        f"[LightRAG Ingest] Found {len(txt_files)} text/markdown and "
        f"{len(pdf_files)} PDF files"
    )

    doc_stats: list[dict] = []

    for filepath in all_files:
        filename = os.path.basename(filepath)

        if filepath.endswith(".pdf"):
            print(f"  Converting PDF: {filename}...")
            text = pdf_to_markdown(filepath)
        else:
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()

        if not text.strip():
            print(f"  Skipping empty file: {filename}")
            continue

        token_count = _count_tokens(text, embedding_model)
        doc_stats.append({
            "filename": filename,
            "char_count": len(text),
            "token_count": token_count,
        })

        print(f"  Inserting {filename} ({len(text)} chars, ~{token_count} tokens)...")
        await rag.ainsert(text)
        print(f"  Done: {filename}")

    print(f"[LightRAG Ingest] Ingestion complete. Graph stored in {working_dir}")

    # --- Write token log ---
    results_dir = os.path.join(PROJECT_ROOT, "results")
    os.makedirs(results_dir, exist_ok=True)
    log_filename = f"ingestion_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.json"
    log_path = os.path.join(results_dir, log_filename)

    log = {
        "ingestion_type": "lightrag",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "embedding_model": embedding_model,
        "generation_model": generation_model,
        "documents": doc_stats,
        "totals": {
            "document_count": len(doc_stats),
            "input_tokens_estimated": sum(d["token_count"] for d in doc_stats),
        },
        "note": (
            "LightRAG manages LLM and embedding API calls internally. "
            "input_tokens_estimated reflects raw document token counts; "
            "actual API usage (entity extraction, chunking) is higher."
        ),
    }

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2)

    print(f"[LightRAG Ingest] Token log written to {log_path}")


def ingest(config_path: str | None = None) -> None:
    """Synchronous entry point for LightRAG ingestion.

    Args:
        config_path: Optional path to ``settings.yaml``.
    """
    asyncio.run(ingest_async(config_path))


if __name__ == "__main__":
    ingest()
