#!/usr/bin/env bash
set -eo pipefail

TESTBED_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${TESTBED_DIR}"

echo "========================================================================"
echo "⚡ Running Phase 24 Offline LoGRA/NoRA Evolution Benchmark"
echo "========================================================================"
python3 benchmark_autonomous_logra.py

echo ""
echo "========================================================================"
echo "🧪 Running Unit & Machine Verification Gate Tests"
echo "========================================================================"
pytest . -v

echo ""
echo "========================================================================"
echo "🔍 Validating Epistemic Verification Receipt"
echo "========================================================================"
python3 -c "
import json
metrics = json.load(open('autonomous_logra_metrics.json'))
receipt = json.load(open('/tmp/hermes_verified_receipt.json'))

assert metrics['temporal_mutual_exclusion_verified'] is True, 'TME check failed'
assert metrics['peak_total_vram_mib'] <= 4812.0, f'Peak VRAM exceeded: {metrics[\"peak_total_vram_mib\"]}'
assert metrics['nora_frobenius_norm'] == 1.0, f'NoRA Frobenius norm != 1.0: {metrics[\"nora_frobenius_norm\"]}'
assert metrics['kl_divergence'] <= 0.05, f'KL divergence exceeded: {metrics[\"kl_divergence\"]}'
assert metrics['post_resume_mtp_tok_per_sec'] >= 42.4, f'MTP rate too low: {metrics[\"post_resume_mtp_tok_per_sec\"]}'
assert receipt['exitstatus'] == 0, 'Receipt exitstatus != 0'

print('✅ Phase 24 Machine Verification Gate: 100% Passed!')
"
