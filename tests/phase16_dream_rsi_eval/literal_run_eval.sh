#!/usr/bin/env bash
set -eo pipefail

TESTBED_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "=== Running Phase 16 DreamRSI, MASS Meta-Loop & RRSI Stability Gate Evaluation ==="
echo "Testbed: ${TESTBED_DIR}"

cd "${TESTBED_DIR}"

# 1. Run benchmark to calculate DreamRSI replay, MASS 3-pass metrics, RRSI gate, and write report
python3 "${TESTBED_DIR}/benchmark_dream_rsi.py"

# 2. Run pytest across scenario unit tests and verification suite
pytest "${TESTBED_DIR}/scenario/test_dream_engine.py" "${TESTBED_DIR}/test_verify.py" -q

# 3. Assert Phase 16 machine verification gate criteria from Evolution.md Section 4.1
python3 -c "import json; d=json.load(open('${TESTBED_DIR}/dream_replay_results.json')); assert d['simulated_calls_reduction_ratio'] >= 1.40 and d['harness2_worktree_compose_gain'] > 0.0 and d['rrsi_stability_margin_exceeded'] is True and d['held_out_pytest_exit_code'] == 0"

# 4. Assert cryptographic epistemic receipt verification
python3 -c "import json; r=json.load(open('/tmp/hermes_verified_receipt.json')); assert r['exitstatus'] == 0 and 'scenario/dream_engine.py' in r['modified']"

echo "PASS: Phase 16 DreamRSI Replay, MASS Meta-Loop & RRSI Stability Gate Certified Cleanly!"
