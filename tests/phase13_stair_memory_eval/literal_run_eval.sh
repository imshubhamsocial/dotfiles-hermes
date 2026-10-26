#!/usr/bin/env bash
set -eo pipefail

TESTBED_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "=== Running Phase 13 STAIR Testbed Evaluation ==="
echo "Testbed: ${TESTBED_DIR}"

python3 "${TESTBED_DIR}/benchmark_stair.py"
pytest "${TESTBED_DIR}/test_verify.py" -q

python3 -c "import json; d=json.load(open('${TESTBED_DIR}/metrics.json')); assert d['recall_at_1'] >= 0.826 and d['chunk_boundary_errors'] == 0 and d['phase13_certified'] is True"

echo "PASS: Phase 13 STAIR Benchmark Certified Cleanly!"
