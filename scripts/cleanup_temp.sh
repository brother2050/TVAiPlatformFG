#!/usr/bin/env bash
# Clean up temp files older than 24 hours
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEMP_DIR="${PROJECT_ROOT}/outputs/temp"

if [[ ! -d "$TEMP_DIR" ]]; then
    mkdir -p "$TEMP_DIR"
    echo "Created $TEMP_DIR"
    exit 0
fi

count=$(find "$TEMP_DIR" -type f -mmin +1440 2>/dev/null | wc -l)

if [[ "$count" -gt 0 ]]; then
    find "$TEMP_DIR" -type f -mmin +1440 -delete
    echo "[$(date -Iseconds)] Cleaned $count temp files from $TEMP_DIR"
else
    echo "[$(date -Iseconds)] No temp files older than 24h"
fi
