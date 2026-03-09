#!/usr/bin/env bash
# =============================================================================
# orchestrator.sh — Run the full RAG evaluation pipeline
# =============================================================================
#
# Orchestrates the end-to-end evaluation process:
#   1. (Optional) Set up virtual environments
#   2. Ingest GDPR documents into ChromaDB and LightRAG
#   3. Run each RAG approach in its own venv
#   4. Evaluate all outputs with DeepEval
#
# Each approach runs in its own virtual environment to avoid dependency
# conflicts. Results are written to outputs/ and evaluation results to
# results/.
#
# Usage:
#   ./orchestrator.sh                  # Run everything end-to-end
#   ./orchestrator.sh --setup          # Create venvs only
#   ./orchestrator.sh --ingest         # Run ingestion only
#   ./orchestrator.sh --run lightrag   # Run one approach
#   ./orchestrator.sh --run all        # Run all approaches
#   ./orchestrator.sh --evaluate       # Run evaluation only
#   ./orchestrator.sh --skip-ingest    # Skip ingestion, run approaches + eval
#
# Options:
#   --max-workers N    Max parallel workers per approach (default: 1)
#   --questions PATH   Custom questions JSON path
#   --approaches LIST  Comma-separated list of approaches to run
#                      (default: lightrag,agentic_rag,crag)
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENVS_DIR="$SCRIPT_DIR/.venvs"
OUTPUTS_DIR="$SCRIPT_DIR/outputs"
RESULTS_DIR="$SCRIPT_DIR/results"

# Defaults
MAX_WORKERS=1
QUESTIONS=""
APPROACHES="lightrag,agentic_rag,crag"
MODE="all"  # all | setup | ingest | run | evaluate
RUN_TARGET=""
SKIP_INGEST=false
INGEST_TARGET="all"

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --setup)
            MODE="setup"
            shift
            ;;
        --ingest)
            MODE="ingest"
            shift
            ;;
        --ingest-target)
            INGEST_TARGET="$2"
            shift 2
            ;;
        --run)
            MODE="run"
            RUN_TARGET="${2:-all}"
            shift 2
            ;;
        --evaluate)
            MODE="evaluate"
            shift
            ;;
        --skip-ingest)
            SKIP_INGEST=true
            shift
            ;;
        --max-workers)
            MAX_WORKERS="$2"
            shift 2
            ;;
        --questions)
            QUESTIONS="$2"
            shift 2
            ;;
        --approaches)
            APPROACHES="$2"
            shift 2
            ;;
        --help|-h)
            head -30 "$0" | grep '^#' | sed 's/^# *//'
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
log() {
    echo ""
    echo "============================================="
    echo "  $1"
    echo "============================================="
}

run_in_venv() {
    local venv_name="$1"
    shift
    local venv_path="$VENVS_DIR/$venv_name"

    if [ ! -d "$venv_path" ]; then
        echo "ERROR: Venv '$venv_name' not found. Run ./setup_envs.sh first."
        exit 1
    fi

    # Run the command using the venv's Python
    "$venv_path/bin/python" "$@"
}

check_envs() {
    if [ ! -d "$VENVS_DIR" ]; then
        echo "Virtual environments not found. Running setup..."
        bash "$SCRIPT_DIR/setup_envs.sh"
    fi
}

# ---------------------------------------------------------------------------
# Stage: Setup
# ---------------------------------------------------------------------------
do_setup() {
    log "Setting up virtual environments"
    bash "$SCRIPT_DIR/setup_envs.sh"
}

# ---------------------------------------------------------------------------
# Stage: Ingestion
# ---------------------------------------------------------------------------
do_ingest() {
    log "Ingesting GDPR documents (target: $INGEST_TARGET)"

    if [ "$INGEST_TARGET" = "all" ] || [ "$INGEST_TARGET" = "chromadb" ]; then
        echo "--- ChromaDB ingestion ---"
        run_in_venv "ingestion" "$SCRIPT_DIR/ingestion/ingest_chromadb.py"
    fi

    if [ "$INGEST_TARGET" = "all" ] || [ "$INGEST_TARGET" = "lightrag" ]; then
        echo "--- LightRAG ingestion ---"
        run_in_venv "ingestion" "$SCRIPT_DIR/ingestion/ingest_lightrag.py"
    fi
}

# ---------------------------------------------------------------------------
# Stage: Run approaches
# ---------------------------------------------------------------------------
run_approach() {
    local approach="$1"
    local extra_args=""

    if [ -n "$QUESTIONS" ]; then
        extra_args="$extra_args --questions $QUESTIONS"
    fi
    extra_args="$extra_args --max-workers $MAX_WORKERS"
    extra_args="$extra_args --output-dir $OUTPUTS_DIR"

    case "$approach" in
        lightrag)
            log "Running: LightRAG"
            run_in_venv "lightrag" \
                "$SCRIPT_DIR/approaches/lightrag_approach/run.py" \
                $extra_args
            ;;
        agentic_rag)
            log "Running: Agentic RAG"
            run_in_venv "agentic_rag" \
                "$SCRIPT_DIR/approaches/agentic_rag/run.py" \
                $extra_args
            ;;
        crag)
            log "Running: CRAG"
            run_in_venv "crag" \
                "$SCRIPT_DIR/approaches/crag/run.py" \
                $extra_args
            ;;
        *)
            echo "ERROR: Unknown approach '$approach'"
            echo "Available: lightrag, agentic_rag, crag"
            exit 1
            ;;
    esac
}

do_run() {
    local target="${1:-all}"
    mkdir -p "$OUTPUTS_DIR"

    if [ "$target" = "all" ]; then
        IFS=',' read -ra APPROACH_LIST <<< "$APPROACHES"
        for approach in "${APPROACH_LIST[@]}"; do
            approach=$(echo "$approach" | xargs)  # trim whitespace
            run_approach "$approach"
        done
    else
        run_approach "$target"
    fi
}

# ---------------------------------------------------------------------------
# Stage: Evaluation
# ---------------------------------------------------------------------------
do_evaluate() {
    log "Evaluating outputs with DeepEval"
    mkdir -p "$RESULTS_DIR"

    run_in_venv "evaluation" \
        "$SCRIPT_DIR/evaluation/evaluate.py" \
        --input-dir "$OUTPUTS_DIR" \
        --output-dir "$RESULTS_DIR"

    echo ""
    echo "Evaluation complete. Results in: $RESULTS_DIR/"
}

# ---------------------------------------------------------------------------
# Main execution
# ---------------------------------------------------------------------------
echo "============================================="
echo "  RAG Evaluation Pipeline"
echo "  Mode: $MODE"
echo "  Approaches: $APPROACHES"
echo "  Max workers: $MAX_WORKERS"
echo "============================================="

case "$MODE" in
    setup)
        do_setup
        ;;
    ingest)
        check_envs
        do_ingest
        ;;
    run)
        check_envs
        do_run "$RUN_TARGET"
        ;;
    evaluate)
        check_envs
        do_evaluate
        ;;
    all)
        # Full pipeline
        check_envs

        if [ "$SKIP_INGEST" = false ]; then
            do_ingest
        else
            echo "Skipping ingestion (--skip-ingest)"
        fi

        do_run "all"
        do_evaluate

        log "Pipeline complete!"
        echo "Outputs:  $OUTPUTS_DIR/"
        echo "Results:  $RESULTS_DIR/"
        echo ""
        echo "Output files:"
        ls -la "$OUTPUTS_DIR"/*.json 2>/dev/null || echo "  (none)"
        echo ""
        echo "Result files:"
        ls -la "$RESULTS_DIR"/*.json 2>/dev/null || echo "  (none)"
        ;;
esac
