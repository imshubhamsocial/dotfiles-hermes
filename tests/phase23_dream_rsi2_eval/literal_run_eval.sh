#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================================================"
echo "🎯 Executing Phase 23: Dream-RSI 2.0 Replay Simulator Pool Evaluation"
echo "========================================================================"

python3 benchmark_dream_rsi2.py
pytest . -q

python3 -c "
import json
d = json.load(open('dream_rsi2_metrics.json'))
r = json.load(open('/tmp/hermes_verified_receipt.json'))
assert d['cuda_vram_delta_mib'] == 0, 'CUDA VRAM delta must be 0'
assert d['call_reduction_ratio'] >= 2.0, 'Call reduction ratio < 2.0x'
assert d['rrsi_stability_gate_passed'] is True, 'RRSI stability gate failed'
assert d['dream_eval_latency_ms'] <= 50.0, 'Dream eval latency > 50.0 ms'
assert r['exitstatus'] == 0, 'Receipt exitstatus != 0'
print('\n🎉 PHASE 23 VERIFICATION GATE: 100% CERTIFIED & PASSED')
"
