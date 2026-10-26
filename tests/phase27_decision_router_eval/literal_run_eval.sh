#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Running Phase 27 Uncertainty-Gated Decision Router Verification ==="
python3 test_verify.py
echo "=== Phase 27 Benchmark & Machine Verification Complete (Exit 0) ==="
