#!/usr/bin/env bash
set -eo pipefail

TESTBED_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "=== Running Phase 18 Embodied Visual World Model & Arc-AGUI Multimodal Desktop Parity Evaluation ==="
echo "Testbed: ${TESTBED_DIR}"

cd "${TESTBED_DIR}"

# 1. Run benchmark script generating metrics
python3 "${TESTBED_DIR}/benchmark_arc_agui.py"

# 2. Run pytest across scenario unit tests and verification suite
pytest "${TESTBED_DIR}/scenario/test_gui_world_model.py" "${TESTBED_DIR}/test_verify.py" -q

# 3. Assert Phase 18 machine verification gate criteria from Evolution.md Section 4.1
python3 -c "import json; v=json.load(open('${TESTBED_DIR}/world_model_metrics.json')); assert v['port_8139_cuda_vram_mib'] == 0 and v['predictive_gui_verification_accuracy'] >= 0.95 and v['anomalous_modal_halt_triggered'] is True"

# 4. Assert cryptographic epistemic receipt verification
python3 -c "import json; r=json.load(open('/tmp/hermes_verified_receipt.json')); assert r['exitstatus'] == 0 and 'scenario/gui_world_model.py' in r['modified']"

echo "PASS: Phase 18 Embodied Visual World Model & Arc-AGUI Desktop Parity Certified Cleanly!"
