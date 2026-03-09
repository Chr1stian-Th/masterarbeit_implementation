#!/usr/bin/env python3
"""
Ingest GDPR text documents into ChromaDB.

Reads ``.txt`` and ``.md`` files from the configured GDPR data directory,
splits them into overlapping chunks, generates embeddings via OpenAI, and
stores everything in a persistent ChromaDB collection.

This collection is shared between the Agentic RAG and CRAG approaches.

Usage:
    python ingestion/ingest_chromadb.py

Environment Variables:
    OPENAI_API_KEY: Required. Your OpenAI API key.
    OPENAI_BASE_URL: Optional. Custom API base URL.
"""

import os
import sys
import glob
import hashlib

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Path setup: ensure project root is on sys.path for common imports
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INGESTION_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, INGESTION_DIR)

from approaches.common.config_loader import load_config

# Load environment variables from ingestion/.env
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

import chromadb
from chromadb.config import Settings
from openai import OpenAI
import tiktoken

from pdf_utils import pdf_to_markdown


def count_tokens(text: str, model: str = "text-embedding-3-small") -> int:
    """Count the number of tokens in a text string.

    Args:
        text: The text to tokenize.
        model: The model whose tokenizer to use.

    Returns:
        Number of tokens.
    """
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


def chunk_text(
    text: str,
    chunk_size: int = 512,
    chunk_overlap: int = 64,
    separator: str = "\n\n",
) -> list[str]:
    """Split text into overlapping chunks by token count.

    First splits on the separator, then groups segments into chunks
    that respect the token budget with overlap.

    Args:
        text: The full document text.
        chunk_size: Maximum tokens per chunk.
        chunk_overlap: Number of overlapping tokens between consecutive chunks.
        separator: Primary split boundary (e.g., paragraph break).

    Returns:
        List of text chunk strings.
    """
    segments = text.split(separator)
    segments = [s.strip() for s in segments if s.strip()]

    chunks = []
    current_segments: list[str] = []
    current_tokens = 0

    for segment in segments:
        seg_tokens = count_tokens(segment)

        # If a single segment exceeds chunk_size, split it further by sentences
        if seg_tokens > chunk_size:
            # Flush current buffer
            if current_segments:
                chunks.append(separator.join(current_segments))
                current_segments = []
                current_tokens = 0

            # Split long segment by sentences
            sentences = segment.replace(". ", ".\n").split("\n")
            for sentence in sentences:
                sent_tokens = count_tokens(sentence)
                if current_tokens + sent_tokens > chunk_size and current_segments:
                    chunks.append(" ".join(current_segments))
                    # Keep overlap
                    overlap_segments = []
                    overlap_tokens = 0
                    for s in reversed(current_segments):
                        t = count_tokens(s)
                        if overlap_tokens + t > chunk_overlap:
                            break
                        overlap_segments.insert(0, s)
                        overlap_tokens += t
                    current_segments = overlap_segments
                    current_tokens = overlap_tokens
                current_segments.append(sentence)
                current_tokens += sent_tokens
            continue

        if current_tokens + seg_tokens > chunk_size and current_segments:
            chunks.append(separator.join(current_segments))

            # Keep overlap from the tail of current_segments
            overlap_segments = []
            overlap_tokens = 0
            for s in reversed(current_segments):
                t = count_tokens(s)
                if overlap_tokens + t > chunk_overlap:
                    break
                overlap_segments.insert(0, s)
                overlap_tokens += t
            current_segments = overlap_segments
            current_tokens = overlap_tokens

        current_segments.append(segment)
        current_tokens += seg_tokens

    # Flush remaining
    if current_segments:
        chunks.append(separator.join(current_segments))

    return chunks


def generate_embeddings(
    client: OpenAI, texts: list[str], model: str
) -> list[list[float]]:
    """Generate embeddings for a batch of texts.

    Args:
        client: Initialized OpenAI client.
        texts: List of text strings to embed.
        model: Embedding model identifier.

    Returns:
        List of embedding vectors.
    """
    response = client.embeddings.create(model=model, input=texts)
    return [item.embedding for item in response.data]


def generate_chunk_id(text: str, source: str, chunk_index: int) -> str:
    """Generate a deterministic ID for a chunk to enable idempotent upserts.

    Args:
        text: The chunk text content.
        source: The source filename.
        chunk_index: The position of this chunk within the source document.

    Returns:
        A hex digest string used as the ChromaDB document ID.
    """
    content = f"{source}::{chunk_index}::{text[:200]}"
    return hashlib.md5(content.encode()).hexdigest()


def ingest(config_path: str | None = None) -> None:
    """Run the full ChromaDB ingestion pipeline.

    Steps:
        1. Load GDPR text files from the data directory.
        2. Chunk each document with configurable size and overlap.
        3. Generate embeddings via OpenAI.
        4. Upsert chunks into a persistent ChromaDB collection.

    Args:
        config_path: Optional path to ``settings.yaml``.
    """
    cfg = load_config(config_path)
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required.")

    base_url = os.environ.get("OPENAI_BASE_URL")
    client_kwargs = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url
    openai_client = OpenAI(**client_kwargs)

    embedding_model = cfg["models"]["embedding_model"]
    chunk_size = cfg["ingestion"]["chunk_size"]
    chunk_overlap = cfg["ingestion"]["chunk_overlap"]
    separator = cfg["ingestion"]["separator"]
    data_dir = os.path.join(PROJECT_ROOT, cfg["ingestion"]["gdpr_data_dir"])
    persist_dir = os.path.join(PROJECT_ROOT, cfg["chromadb"]["persist_directory"])
    collection_name = cfg["chromadb"]["collection_name"]

    # --- Load documents ---
    txt_files = sorted(
        glob.glob(os.path.join(data_dir, "*.txt"))
        + glob.glob(os.path.join(data_dir, "*.md"))
    )
    pdf_files = sorted(glob.glob(os.path.join(data_dir, "*.pdf")))
    all_files = txt_files + pdf_files

    if not all_files:
        print(f"[Ingest] No .txt, .md, or .pdf files found in {data_dir}")
        print(f"[Ingest] Please place GDPR document files in {data_dir}")
        return

    print(
        f"[Ingest] Found {len(txt_files)} text/markdown and "
        f"{len(pdf_files)} PDF files in {data_dir}"
    )

    # --- Chunk documents ---
    all_chunks: list[str] = []
    all_metadatas: list[dict] = []
    all_ids: list[str] = []

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

        chunks = chunk_text(text, chunk_size, chunk_overlap, separator)
        print(f"  {filename}: {len(chunks)} chunks")

        for i, chunk in enumerate(chunks):
            chunk_id = generate_chunk_id(chunk, filename, i)
            all_chunks.append(chunk)
            all_metadatas.append({
                "source": filename,
                "chunk_index": i,
                "total_chunks": len(chunks),
            })
            all_ids.append(chunk_id)

    print(f"[Ingest] Total chunks to embed: {len(all_chunks)}")

    # --- Generate embeddings in batches ---
    batch_size = 100
    all_embeddings: list[list[float]] = []

    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i : i + batch_size]
        embeddings = generate_embeddings(openai_client, batch, embedding_model)
        all_embeddings.extend(embeddings)
        print(f"  Embedded batch {i // batch_size + 1}/{(len(all_chunks) - 1) // batch_size + 1}")

    # --- Store in ChromaDB ---
    chroma_client = chromadb.PersistentClient(
        path=persist_dir,
        settings=Settings(anonymized_telemetry=False),
    )

    # Delete and recreate collection for idempotent ingestion
    try:
        chroma_client.delete_collection(collection_name)
    except Exception:
        pass

    collection = chroma_client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": cfg["chromadb"]["distance_metric"]},
    )

    # Upsert in batches (ChromaDB limit)
    chroma_batch_size = 5000
    for i in range(0, len(all_chunks), chroma_batch_size):
        end = min(i + chroma_batch_size, len(all_chunks))
        collection.upsert(
            ids=all_ids[i:end],
            documents=all_chunks[i:end],
            embeddings=all_embeddings[i:end],
            metadatas=all_metadatas[i:end],
        )

    print(f"[Ingest] Successfully ingested {collection.count()} chunks into ChromaDB")
    print(f"[Ingest] Collection: {collection_name} at {persist_dir}")


if __name__ == "__main__":
    ingest()
