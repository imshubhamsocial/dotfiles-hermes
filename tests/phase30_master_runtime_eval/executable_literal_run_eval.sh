#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Running Phase 30 Production Omniscient Master Gate Verification ==="
python3 test_verify.py
echo "=== Phase 30 Benchmark & Machine Verification Complete (Exit 0) ==="
