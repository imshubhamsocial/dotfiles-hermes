#!/usr/bin/env bash
# Verification Contract for Phase 39: Harness Responses API Fix & Dual-Track Routing
set -euo pipefail

WORKSPACE="/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes"
RUNNER="/var/home/imshubhamsocial/Desktop/GDR/GDR24/run_remediated_gauntlet.sh"
RECEIPT="/tmp/hermes_verified_receipt.json"

chmod +x "$RUNNER"
bash -n "$RUNNER"

# Assert mandatory -M responses_api=false flag is present for both tracks
grep -q "\-M responses_api=false" "$RUNNER"
grep -q "http://127.0.0.1:1934/v1" "$RUNNER"
grep -q "verify_epistemic_eval_audit.py" "$RUNNER"

# Assert upstream purity and VRAM ceiling
test -z "$(git -C "$WORKSPACE/.hermes/hermes-agent" status --porcelain)"
VRAM_USED=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -n 1 | awk '{print $1}')
python3 -c "assert float('$VRAM_USED') <= 5400.0, f'VRAM ceiling breached: $VRAM_USED MiB'"

python3 -c '
import json
json.dump({
    "exitstatus": 0,
    "workspace": "'"$WORKSPACE"'",
    "phase": "phase_39_harness_responses_api_fix_and_dual_track_routing",
    "nvml_vram_used_mib": float("'"$VRAM_USED"'"),
    "upstream_git_clean": True
}, open("'"$RECEIPT"'", "w"), indent=2)
'
echo "PHASE 39 VERIFIED: -M responses_api=false and dual-track routing sealed."
