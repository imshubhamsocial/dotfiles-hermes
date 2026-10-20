#!/usr/bin/env bash
# Execute an isolated reproduction script and verify exit code transition
set -euo pipefail

SCRIPT="${1:-reproduce_issue.py}"
if [ ! -f "$SCRIPT" ]; then
    echo "Reproduction script '$SCRIPT' not found." >&2
    exit 1
fi

python3 "$SCRIPT"
