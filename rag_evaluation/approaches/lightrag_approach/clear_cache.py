#!/usr/bin/env python3
"""
Clear the LightRAG LLM response cache.

Usage:
    python approaches/lightrag_approach/clear_cache.py
"""

import os
import sys
import asyncio
from functools import partial

from dotenv import load_dotenv

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from approaches.common.config_loader import load_config

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))


async def main() -> None:
    from lightrag import LightRAG
    from lightrag.llm.openai import openai_complete_if_cache, openai_embed
    from lightrag.utils import EmbeddingFunc

    config = load_config()
    working_dir = os.path.join(PROJECT_ROOT, config["lightrag"]["working_dir"])
    embedding_model = config["models"]["embedding_model"]
    embedding_dim = config["models"]["embedding_dimensions"]
    generation_model = config["models"]["generation_model"]

    api_key = os.environ.get("OPENAI_API_KEY", "dummy")
    base_url = os.environ.get("OPENAI_BASE_URL")
    llm_kwargs = {"api_key": api_key}
    if base_url:
        llm_kwargs["base_url"] = base_url

    rag = LightRAG(
        working_dir=working_dir,
        llm_model_func=partial(openai_complete_if_cache, generation_model, **llm_kwargs),
        llm_model_name=generation_model,
        llm_model_max_async=4,
        embedding_func=EmbeddingFunc(
            embedding_dim=embedding_dim,
            max_token_size=config["lightrag"]["max_token_size"],
            func=partial(openai_embed.func, model=embedding_model, **llm_kwargs),
        ),
    )

    await rag.initialize_storages()
    await rag.aclear_cache()
    await rag.finalize_storages()
    print("LightRAG cache cleared.")


if __name__ == "__main__":
    asyncio.run(main())
