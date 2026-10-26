#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================================================"
echo "🎯 Executing Phase 22: Spec-Kit 2.0 Failure Cluster Annealing Evaluation"
echo "========================================================================"

python3 benchmark_speckit2.py
pytest . -q

python3 -c "
import json
s = json.load(open('speckit2_metrics.json'))
r = json.load(open('/tmp/hermes_verified_receipt.json'))
assert s['cuda_vram_delta_mib'] == 0, 'CUDA VRAM delta must be 0'
assert s['sympy_vram_proof_passed'] is True, 'SymPy VRAM proof failed'
assert s['topological_regen_success'] is True, 'Topological regeneration failed'
assert s['patch_debt_reduction_pct'] >= 60.0, 'Patch debt reduction < 60.0%'
assert r['exitstatus'] == 0, 'Receipt exitstatus != 0'
print('\n🎉 PHASE 22 VERIFICATION GATE: 100% CERTIFIED & PASSED')
"
