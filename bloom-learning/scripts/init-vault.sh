#!/bin/bash
# init-vault.sh — Initialize or resume an Obsidian learning vault for a topic.

set -euo pipefail

usage() {
    cat <<'EOF'
Usage:
  bash init-vault.sh [--resume] <vault-path> <topic-name> [learner-level]

Options:
  --resume   Reuse an existing topic directory if it already contains progress
  --help     Show this help message
EOF
}

RESUME=0
POSITIONAL_ARGS=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --resume)
            RESUME=1
            shift
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            POSITIONAL_ARGS+=("$1")
            shift
            ;;
    esac
done

set -- "${POSITIONAL_ARGS[@]}"

VAULT_PATH="${1:?Error: vault-path is required}"
TOPIC="${2:?Error: topic-name is required}"
LEVEL="${3:-beginner}"
DATE=$(date +%Y-%m-%d)

if [[ "$TOPIC" == *"/"* ]]; then
    echo "Error: topic-name cannot contain '/'" >&2
    exit 1
fi

TOPIC_DIR="${VAULT_PATH}/${TOPIC}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEMPLATE_DIR="${SCRIPT_DIR}/../assets/templates"
PYTHON_BIN="${PYTHON_BIN:-}"
if [ -z "$PYTHON_BIN" ]; then
    if command -v python >/dev/null 2>&1 && python --version >/dev/null 2>&1; then
        PYTHON_BIN="python"
    elif command -v python3 >/dev/null 2>&1 && python3 --version >/dev/null 2>&1; then
        PYTHON_BIN="python3"
    else
        echo "Error: python is required to render templates." >&2
        exit 1
    fi
fi

render_template() {
    local template_path="$1"
    local output_path="$2"
    TOPIC_VALUE="$TOPIC" LEVEL_VALUE="$LEVEL" DATE_VALUE="$DATE" "$PYTHON_BIN" - "$template_path" "$output_path" <<'PY'
import os
import sys
from pathlib import Path

template_path = Path(sys.argv[1])
output_path = Path(sys.argv[2])
content = template_path.read_text(encoding="utf-8")
replacements = {
    "{{TOPIC}}": os.environ["TOPIC_VALUE"],
    "{{LEVEL}}": os.environ["LEVEL_VALUE"],
    "{{DATE}}": os.environ["DATE_VALUE"],
}
for placeholder, value in replacements.items():
    content = content.replace(placeholder, value)
output_path.write_text(content, encoding="utf-8")
PY
}

bootstrap_missing_state() {
    if [ ! -f "${TOPIC_DIR}/_meta/state.json" ] && [ -f "${TEMPLATE_DIR}/state.json" ]; then
        render_template "${TEMPLATE_DIR}/state.json" "${TOPIC_DIR}/_meta/state.json"
    fi

    if [ ! -f "${TOPIC_DIR}/_meta/state-lite.json" ] && [ -f "${TEMPLATE_DIR}/state-lite.json" ]; then
        render_template "${TEMPLATE_DIR}/state-lite.json" "${TOPIC_DIR}/_meta/state-lite.json"
    fi

    if [ ! -f "${TOPIC_DIR}/_meta/current.md" ] && [ -f "${TEMPLATE_DIR}/current.md" ]; then
        render_template "${TEMPLATE_DIR}/current.md" "${TOPIC_DIR}/_meta/current.md"
    fi

    mkdir -p "${TOPIC_DIR}/_meta/sessions"
}

if [ -d "$TOPIC_DIR" ] && [ -f "${TOPIC_DIR}/_meta/progress.md" ]; then
    if [ "$RESUME" -eq 1 ]; then
        bootstrap_missing_state
        echo "Resuming existing topic: ${TOPIC_DIR}"
        exit 0
    fi

    echo "Warning: Directory '${TOPIC_DIR}' already exists."
    echo "Found existing progress. Use --resume to continue, or remove the directory to restart."
    exit 1
fi

echo "Creating vault structure for: ${TOPIC}"
mkdir -p "${TOPIC_DIR}/_meta/sessions" "${TOPIC_DIR}/notes" "${TOPIC_DIR}/exercises" "${TOPIC_DIR}/summaries" "${TOPIC_DIR}/projects"

if [ -d "$TEMPLATE_DIR" ]; then
    render_template "${TEMPLATE_DIR}/current.md" "${TOPIC_DIR}/_meta/current.md"
    render_template "${TEMPLATE_DIR}/progress.md" "${TOPIC_DIR}/_meta/progress.md"
    render_template "${TEMPLATE_DIR}/knowledge-map.md" "${TOPIC_DIR}/_meta/knowledge-map.md"
    render_template "${TEMPLATE_DIR}/spaced-repetition.md" "${TOPIC_DIR}/_meta/spaced-repetition.md"
    render_template "${TEMPLATE_DIR}/state.json" "${TOPIC_DIR}/_meta/state.json"
    render_template "${TEMPLATE_DIR}/state-lite.json" "${TOPIC_DIR}/_meta/state-lite.json"
else
    echo "Warning: Template directory not found at ${TEMPLATE_DIR}"
    echo "Creating minimal placeholder files..."
    echo "# Current Learning State: ${TOPIC}" > "${TOPIC_DIR}/_meta/current.md"
    echo "# Learning Progress: ${TOPIC}" > "${TOPIC_DIR}/_meta/progress.md"
    echo "# Knowledge Map: ${TOPIC}" > "${TOPIC_DIR}/_meta/knowledge-map.md"
    echo "# Spaced Repetition Schedule" > "${TOPIC_DIR}/_meta/spaced-repetition.md"
    echo '{"topic": "'"${TOPIC}"'", "updated_at": "'"${DATE}"'", "current": {"module": "Module 1", "concept": "1.1"}}' > "${TOPIC_DIR}/_meta/state-lite.json"
    cat > "${TOPIC_DIR}/_meta/state.json" <<EOF
{"topic": "${TOPIC}", "created_at": "${DATE}", "learner": {"level": "${LEVEL}"}}
EOF
fi

echo ""
echo "Vault initialized successfully:"
echo "  ${TOPIC_DIR}/"
echo "  ├── _meta/"
echo "  │   ├── current.md"
echo "  │   ├── progress.md"
echo "  │   ├── knowledge-map.md"
echo "  │   ├── spaced-repetition.md"
echo "  │   ├── state-lite.json"
echo "  │   ├── state.json"
echo "  │   └── sessions/"
echo "  ├── notes/"
echo "  ├── exercises/"
echo "  ├── summaries/"
echo "  └── projects/"
echo ""
echo "Topic: ${TOPIC}"
echo "Level: ${LEVEL}"
echo "Date:  ${DATE}"
echo ""
echo "Ready to start learning. Open in Obsidian and begin a session."
