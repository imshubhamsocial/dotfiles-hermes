#!/usr/bin/env bash
set -eo pipefail

TESTBED_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "=== Running Phase 17 TTC Scaling & Hibernate-and-Train LoGRA/NoRA Evaluation ==="
echo "Testbed: ${TESTBED_DIR}"

cd "${TESTBED_DIR}"

# 1. Run benchmark script executing hibernate training telemetry
python3 "${TESTBED_DIR}/benchmark_logra_nora.py"

# 2. Run pytest across scenario unit tests and verification suite
pytest "${TESTBED_DIR}/scenario/test_logra_aligner.py" "${TESTBED_DIR}/test_verify.py" -q

# 3. Assert Phase 17 machine verification gate criteria from Evolution.md Section 4.1
python3 -c "import json; t=json.load(open('${TESTBED_DIR}/training_telemetry.json')); assert t['peak_total_vram_mib'] <= 4812 and t['nora_frobenius_norm_init'] == 1.0 and t['kl_budget_respected'] is True and t['post_resume_mtp_tok_per_sec'] >= 39.7"

# 4. Assert cryptographic epistemic receipt verification
python3 -c "import json; r=json.load(open('/tmp/hermes_verified_receipt.json')); assert r['exitstatus'] == 0 and 'scenario/logra_aligner.py' in r['modified']"

echo "PASS: Phase 17 TTC Scaling & Hibernate LoGRA/NoRA Weight Evolution Certified Cleanly!"
