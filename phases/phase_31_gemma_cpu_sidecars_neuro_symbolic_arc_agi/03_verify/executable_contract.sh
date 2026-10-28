#!/usr/bin/env bash
# Verification Contract (V_contract) for Realigned Phase 31: Gemma CPU Sidecar Verification
set -euo pipefail

WORKSPACE="/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes"
RECEIPT_FILE="/tmp/hermes_verified_receipt.json"

export PATH="$WORKSPACE/.local/bin:$PATH"

# 1. Execute verification inside workspace environment
python3 -c '
import sys
from pathlib import Path

sys.path.insert(0, ".hermes")
import mcp_openjev as m

# Verify CPU embedding sidecar operates with valid L2 normalization under 25ms latency
res = m.jev_gemma_sidecar_embed_and_refine(
    "Resolve race condition in _drain_loop",
    ["worker_pool.py:_drain_loop", "general docstring"]
)
assert res["l2_norm_verified"] is True, "L2 normalization verification failed"
lat = res["latency_ms"]
assert lat < 25.0, f"Latency threshold breached: {lat}ms"

# Verify mock solver tool has been purged from module namespace
assert not hasattr(m, "jev_arc_agi_neurosymbolic_solve"), "CRITICAL: Mock tool jev_arc_agi_neurosymbolic_solve still present in module!"

# Verify VRAM is unaffected (CPU execution)
assert res["cuda_delta_mib"] == 0.0, "CPU sidecar contaminated GPU VRAM"

import json
json.dump({
    "exitstatus": 0,
    "workspace": "'"$WORKSPACE"'",
    "phase": "phase_31_gemma_cpu_sidecars_neuro_symbolic_arc_agi",
    "tested": ["jev_gemma_sidecar_embed_and_refine"],
    "excised": ["jev_arc_agi_neurosymbolic_solve"],
    "modified": [".hermes/mcp_openjev.py", ".hermes/SOUL.md"]
}, open("'"$RECEIPT_FILE"'", "w"))
'

# 2. Assert receipt validity and zero benchmark stubs in codebase
test -f "$RECEIPT_FILE"
python3 -c 'import json; r = json.load(open("'"$RECEIPT_FILE"'")); assert r["exitstatus"] == 0'
! grep -rn "jev_arc_agi_neurosymbolic_solve" "$WORKSPACE/.hermes/"
! grep -rn "def transform(grid):" "$WORKSPACE/.hermes/mcp_openjev.py"
echo "PHASE 31 REALIGNMENT VERIFIED: Codebase clean, CPU sidecar operational."
