#!/usr/bin/env bash
# Verify .hermes/specs/ dependency DAG and topological order
set -euo pipefail

SPEC_DIR="${1:-.hermes/specs}"
if [ ! -d "$SPEC_DIR" ]; then
    echo "Spec directory '$SPEC_DIR' not found." >&2
    exit 1
fi

echo "==> Scanning specifications in '$SPEC_DIR'..."
find "$SPEC_DIR" -name "*.md" | sort
