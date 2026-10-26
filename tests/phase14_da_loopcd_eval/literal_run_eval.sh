#!/usr/bin/env bash
set -eo pipefail

TESTBED_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "=== Running Phase 14 Declarative Attention & LoopCD Testbed Evaluation ==="
echo "Testbed: ${TESTBED_DIR}"

python3 "${TESTBED_DIR}/benchmark_da_loopcd.py"
pytest "${TESTBED_DIR}/test_verify.py" -q

python3 -c "import json; m=json.load(open('${TESTBED_DIR}/metrics.json')); assert m['attended_token_reduction_pct'] >= 48.0 and m['loopcd_pass_at_1_gain'] > 0.0 and m['phase14_certified'] is True"

echo "PASS: Phase 14 Declarative Attention & LoopCD Benchmark Certified Cleanly!"
