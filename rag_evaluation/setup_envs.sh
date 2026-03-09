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
#   - Python 3.10+ (python3 must be on PATH)
#   - pip (included with Python 3.10+)
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENVS_DIR="$SCRIPT_DIR/.venvs"
PYTHON="${PYTHON:-python3}"

echo "============================================="
echo "  RAG Evaluation - Environment Setup"
echo "============================================="
echo "Python: $($PYTHON --version)"
echo "Venvs directory: $VENVS_DIR"
echo ""

mkdir -p "$VENVS_DIR"

# ---------------------------------------------------------------------------
# Use the D drive for pip's temp and cache dirs to avoid exhausting tmpfs
# ---------------------------------------------------------------------------
PIP_TMP_DIR="/mnt/d/tmp/pip"
mkdir -p "$PIP_TMP_DIR"
export TMPDIR="$PIP_TMP_DIR"
export PIP_CACHE_DIR="$PIP_TMP_DIR/cache"

echo "Pip temp/cache dir: $PIP_TMP_DIR"
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
        $PYTHON -m venv "$venv_path"
    fi

    # Activate and install
    source "$venv_path/bin/activate"
    pip install --upgrade pip --quiet
    pip install -r "$requirements" --quiet
    deactivate

    echo "  Done: $name"
    echo ""
}

# ---------------------------------------------------------------------------
# Create venvs for each component
# ---------------------------------------------------------------------------

# 1. Ingestion (used for both ChromaDB and LightRAG ingestion)
setup_venv "ingestion" "$SCRIPT_DIR/ingestion/requirements.txt"

# Also install LightRAG in the ingestion venv for ingest_lightrag.py
source "$VENVS_DIR/ingestion/bin/activate"
pip install lightrag-hku --quiet
deactivate

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
