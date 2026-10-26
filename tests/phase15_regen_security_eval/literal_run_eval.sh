#!/usr/bin/env bash
set -eo pipefail

TESTBED_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "=== Running Phase 15 OpenJEV, FastEmbed CPU, Open-Notebook & Spec-Graph Evaluation ==="
echo "Testbed: ${TESTBED_DIR}"

cd "${TESTBED_DIR}"

# 1. Run benchmark to calculate SymPy budget, FastEmbed CPU status, Open-Notebook config, and write report
python3 "${TESTBED_DIR}/benchmark_regen_security.py"

# 2. Run pytest across scenario unit tests and verification suite
pytest "${TESTBED_DIR}/scenario/test_sanitizer.py" "${TESTBED_DIR}/test_verify.py" -q

# 3. Assert Phase 15 machine verification gate criteria from Evolution.md
python3 -c "import json; s=json.load(open('${TESTBED_DIR}/security_regen_report.json')); assert s['sympy_vram_bound_verified'] is True and s['fastembed_cuda_mib'] == 0 and s['open_notebook_mcp_connected'] is True and s['memory_poisoning_blocked'] == 100 and s['regen_roundoff_error'] < 1e-6"

# 4. Assert cryptographic epistemic receipt verification
python3 -c "import json; r=json.load(open('/tmp/hermes_verified_receipt.json')); assert r['exitstatus'] == 0 and 'scenario/sanitizer_engine.py' in r['modified']"

echo "PASS: Phase 15 OpenJEV, FastEmbed CPU, Open-Notebook & Spec-Graph Benchmark & Verification Certified Cleanly!"
