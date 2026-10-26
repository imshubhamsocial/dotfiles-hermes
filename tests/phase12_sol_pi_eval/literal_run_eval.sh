#!/usr/bin/env bash
set -eo pipefail

TESTBED_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "=== Running Phase 12 SoL-Pi Testbed Evaluation ==="
echo "Testbed: ${TESTBED_DIR}"

python3 "${TESTBED_DIR}/benchmark_sol_pi.py"
pytest "${TESTBED_DIR}" -q

python3 -c "import json; d=json.load(open('${TESTBED_DIR}/metrics.json')); assert d['token_reduction_pct'] >= 44.0 and d['tabu_halt_triggered'] is True and d['verifier_preserved_tracebacks'] is True"

echo "PASS: Phase 12 SoL-Pi Evaluation Certified Cleanly!"
