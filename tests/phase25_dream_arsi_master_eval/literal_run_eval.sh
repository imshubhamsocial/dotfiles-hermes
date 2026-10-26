#!/usr/bin/env bash
set -eo pipefail

TESTBED_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${TESTBED_DIR}"

echo "========================================================================"
echo "⚡ Running Phase 25 Dream-ARSI Master Omniscient Parity Benchmark"
echo "========================================================================"
python3 benchmark_dream_arsi.py

echo ""
echo "========================================================================"
echo "🧪 Running Unit & Machine Verification Gate Tests"
echo "========================================================================"
PYTHONPATH=".:scenario:$PYTHONPATH" pytest . -v

echo ""
echo "========================================================================"
echo "🔍 Validating Epistemic Verification Receipt & Omniscient Parity"
echo "========================================================================"
python3 -c "
import json
m = json.load(open('arsi_master_report.json'))
r = json.load(open('/tmp/hermes_verified_receipt.json'))

assert m['all_14_phases_certified'] is True, 'Not all 14 phases certified'
assert m['peak_online_vram_mib'] <= 4812.0, f'Peak VRAM exceeded: {m[\"peak_online_vram_mib\"]}'
assert m['zero_spoon_feeding_verified'] is True, 'Zero spoon feeding invariant violated'
assert m['chezmoi_sync_clean'] is True, 'Chezmoi sync is not clean'
assert m['argon_gauntlet_challenges_passed'] == 6, f'Argon challenges failed: {m[\"argon_gauntlet_challenges_passed\"]}'
assert r['exitstatus'] == 0, 'Receipt exitstatus != 0'

print('✅ Phase 25 Machine Verification Gate: 100% Passed!')
"
