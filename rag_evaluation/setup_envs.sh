#!/usr/bin/env bash
# =============================================================================
# setup_envs.sh — Create isolated virtual environments for each component
# =============================================================================
#
# Creates separate Python venvs for:
#   - ingestion (ChromaDB + LightRAG data loading)
#   - lightrag_approach (LightRAG query pipeline)
#   - agentic_rag (Agentic RAG pipeline)
#   - crag (Corrective RAG pipeline)
#   - evaluation (DeepEval metrics)
#
# Each venv installs only the dependencies needed for that component,
# preventing version conflicts between approaches.
#
# Usage:
#   chmod +x setup_envs.sh
#   ./setup_envs.sh
#
# Requirements:
#   - uv (https://github.com/astral-sh/uv)
#   - Python 3.10+
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENVS_DIR="$SCRIPT_DIR/.venvs"
UV="${UV:-uv}"

echo "============================================="
echo "  RAG Evaluation - Environment Setup"
echo "============================================="
echo "uv: $($UV --version)"
echo "Venvs directory: $VENVS_DIR"
echo ""

mkdir -p "$VENVS_DIR"

# ---------------------------------------------------------------------------
# Use the D drive for uv's cache dir to avoid exhausting tmpfs
# ---------------------------------------------------------------------------
UV_CACHE_DIR="/mnt/d/tmp/uv-cache"
mkdir -p "$UV_CACHE_DIR"
export UV_CACHE_DIR

echo "uv cache dir: $UV_CACHE_DIR"
echo ""

# ---------------------------------------------------------------------------
# Helper: create a venv and install requirements
# ---------------------------------------------------------------------------
setup_venv() {
    local name="$1"
    local requirements="$2"
    local venv_path="$VENVS_DIR/$name"

    echo "--- Setting up: $name ---"

    if [ -d "$venv_path" ]; then
        echo "  Venv already exists. Reinstalling dependencies..."
    else
        echo "  Creating venv..."
        $UV venv "$venv_path"
    fi

    $UV pip install -r "$requirements" --python "$venv_path/bin/python"

    echo "  Done: $name"
    echo ""
}

# ---------------------------------------------------------------------------
# Create venvs for each component
# ---------------------------------------------------------------------------

# 1. Ingestion (used for both ChromaDB and LightRAG ingestion)
setup_venv "ingestion" "$SCRIPT_DIR/ingestion/requirements.txt"

# Also install LightRAG in the ingestion venv for ingest_lightrag.py
$UV pip install lightrag-hku --python "$VENVS_DIR/ingestion/bin/python"

# 2. LightRAG approach
setup_venv "lightrag" "$SCRIPT_DIR/approaches/lightrag_approach/requirements.txt"

# 3. Agentic RAG approach
setup_venv "agentic_rag" "$SCRIPT_DIR/approaches/agentic_rag/requirements.txt"

# 4. CRAG approach
setup_venv "crag" "$SCRIPT_DIR/approaches/crag/requirements.txt"

# 5. Evaluation
setup_venv "evaluation" "$SCRIPT_DIR/evaluation/requirements.txt"

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo "============================================="
echo "  All environments created successfully!"
echo "============================================="
echo ""
echo "Environments:"
ls -d "$VENVS_DIR"/*/ 2>/dev/null | while read dir; do
    name=$(basename "$dir")
    py_version=$("$dir/bin/python" --version 2>/dev/null || echo "unknown")
    echo "  $name: $py_version"
done
echo ""
echo "Next steps:"
echo "  1. Copy .env.example files and add your API keys:"
echo "     cp ingestion/.env.example ingestion/.env"
echo "     cp approaches/lightrag_approach/.env.example approaches/lightrag_approach/.env"
echo "     cp approaches/agentic_rag/.env.example approaches/agentic_rag/.env"
echo "     cp approaches/crag/.env.example approaches/crag/.env"
echo "     cp evaluation/.env.example evaluation/.env"
echo ""
echo "  2. Place GDPR documents in data/gdpr/"
echo "  3. Place question corpus in data/questions/questions.json"
echo "  4. Run: ./orchestrator.sh"
