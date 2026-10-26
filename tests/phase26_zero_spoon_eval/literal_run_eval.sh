#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Running Phase 26 Zero-Spoon-Feeding Intent Compiler Verification ==="
python3 test_verify.py
echo "=== Phase 26 Benchmark & Machine Verification Complete (Exit 0) ==="
