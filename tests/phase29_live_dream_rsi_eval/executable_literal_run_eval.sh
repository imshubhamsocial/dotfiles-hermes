#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Running Phase 29 Live state.db Dream-RSI 2.0 & MASS Verification ==="
python3 test_verify.py
echo "=== Phase 29 Benchmark & Machine Verification Complete (Exit 0) ==="
