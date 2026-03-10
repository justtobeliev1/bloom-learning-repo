#!/bin/bash
# init-vault.sh — Initialize an Obsidian learning vault for a new topic
#
# Usage: bash init-vault.sh <vault-path> <topic-name> [learner-level]
#
# Arguments:
#   vault-path    Path to the Obsidian vault root
#   topic-name    Name of the topic to learn (used as folder name)
#   learner-level Optional: beginner/intermediate/advanced (default: beginner)
#
# Example:
#   bash init-vault.sh ~/Documents/Obsidian\ Vault "Python装饰器" beginner

set -euo pipefail

VAULT_PATH="${1:?Error: vault-path is required}"
TOPIC="${2:?Error: topic-name is required}"
LEVEL="${3:-beginner}"
DATE=$(date +%Y-%m-%d)

TOPIC_DIR="${VAULT_PATH}/${TOPIC}"

if [ -d "$TOPIC_DIR" ]; then
    echo "Warning: Directory '${TOPIC_DIR}' already exists."
    echo "Checking for existing progress..."
    if [ -f "${TOPIC_DIR}/_meta/progress.md" ]; then
        echo "Found existing progress. Aborting to avoid overwriting."
        echo "To restart, delete the directory first: rm -rf \"${TOPIC_DIR}\""
        exit 1
    fi
fi

# Get the directory where this script lives (to find templates)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEMPLATE_DIR="${SCRIPT_DIR}/../assets/templates"

# Create directory structure
echo "Creating vault structure for: ${TOPIC}"
mkdir -p "${TOPIC_DIR}/_meta"
mkdir -p "${TOPIC_DIR}/notes"
mkdir -p "${TOPIC_DIR}/exercises"
mkdir -p "${TOPIC_DIR}/summaries"
mkdir -p "${TOPIC_DIR}/projects"

# Copy and populate templates
if [ -d "$TEMPLATE_DIR" ]; then
    # Progress
    sed "s/{{TOPIC}}/${TOPIC}/g; s/{{DATE}}/${DATE}/g; s/{{LEVEL}}/${LEVEL}/g" \
        "${TEMPLATE_DIR}/progress.md" > "${TOPIC_DIR}/_meta/progress.md"

    # Knowledge Map
    sed "s/{{TOPIC}}/${TOPIC}/g; s/{{DATE}}/${DATE}/g" \
        "${TEMPLATE_DIR}/knowledge-map.md" > "${TOPIC_DIR}/_meta/knowledge-map.md"

    # Spaced Repetition
    sed "s/{{TOPIC}}/${TOPIC}/g; s/{{DATE}}/${DATE}/g" \
        "${TEMPLATE_DIR}/spaced-repetition.md" > "${TOPIC_DIR}/_meta/spaced-repetition.md"
else
    echo "Warning: Template directory not found at ${TEMPLATE_DIR}"
    echo "Creating minimal placeholder files..."
    echo "# Learning Progress: ${TOPIC}" > "${TOPIC_DIR}/_meta/progress.md"
    echo "# Knowledge Map: ${TOPIC}" > "${TOPIC_DIR}/_meta/knowledge-map.md"
    echo "# Spaced Repetition Schedule" > "${TOPIC_DIR}/_meta/spaced-repetition.md"
fi

echo ""
echo "Vault initialized successfully:"
echo "  ${TOPIC_DIR}/"
echo "  ├── _meta/"
echo "  │   ├── progress.md"
echo "  │   ├── knowledge-map.md"
echo "  │   └── spaced-repetition.md"
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
