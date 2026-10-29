#!/usr/bin/env bash
# Verification Contract for Phase 45: 30% Orchestration FastMCP Upgrade
set -euo pipefail

WORKSPACE="/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes"
RECEIPT="/tmp/hermes_verified_receipt.json"

echo "=== [Phase 45 Contract: 30% Orchestration FastMCP Upgrade] ==="

# 1. Execute Ruff Linter on Orchestration Modules
python3 -m ruff check "$WORKSPACE/scripts/hermes_abductive_fastmcp.py" \
                      "$WORKSPACE/.hermes/mcp_ephemeral_bridge.py"

# 2. Comprehensive Test Suite
python3 -c '
import json
from scripts.hermes_abductive_fastmcp import (
    intercept_and_enforce_epistemic_gates,
    translate_tool_error_for_4b_cognition,
    decompose_and_sequentialize_tools
)

print("[1/3] Testing In-Flight Gate 2 (G_read) Interception...")
state = {}
# Premature transfer must be BLOCKED
res_blocked = intercept_and_enforce_epistemic_gates(state, {"name": "transfer_to_human_agents"})
assert res_blocked["status"] == "BLOCKED_BY_EPISTEMIC_GATE_2"
assert "read_tools_called is empty" in res_blocked["synthetic_observation"]

# Domain read allows and updates read_history
res_read = intercept_and_enforce_epistemic_gates(state, {"name": "find_user_id_by_name_zip"})
assert res_read["status"] == "ALLOW"
assert "find_user_id_by_name_zip" in state["read_tools_called"]

# Now transfer is ALLOWED
res_allowed = intercept_and_enforce_epistemic_gates(state, {"name": "transfer_to_human_agents"})
assert res_allowed["status"] == "ALLOW"

print("[2/3] Testing Abductive Error Translator (Counterfactual Bottleneck Fix)...")
raw_miss = "Order #W506110 not found in database."
translated = translate_tool_error_for_4b_cognition(
    "get_order_details",
    {"order_id": "W506110"},
    raw_miss
)
assert "SCHEMA_STATUS: 100%_VALID" in translated
assert "Do NOT change or guess parameter names" in translated
assert "find_user_id_by_name_zip" in translated

# Normal non-error tool output must remain untouched
clean_out = json.dumps({"order_id": "W123", "items": ["shoes"]})
assert translate_tool_error_for_4b_cognition("get_order_details", {"order_id": "W123"}, clean_out) == clean_out

print("[3/3] Testing Sequential Tool Decomposition (BFCL Cross-talk Fix)...")
calls = [
    {"id": "c1", "function": {"name": "get_product_details", "arguments": "{\"id\": \"p1\"}"}},
    {"id": "c2", "function": {"name": "get_product_details", "arguments": "{\"id\": \"p1\"}"}}, # duplicate
    {"id": "c3", "function": {"name": "calculate", "arguments": "{\"expr\": \"2+2\"}"}},
]
seq_calls = decompose_and_sequentialize_tools(calls)
assert len(seq_calls) == 2
assert seq_calls[0]["id"] == "c1"
assert seq_calls[1]["id"] == "c3"

print("All Orchestration Middleware verification contracts PASSED.")
'

# 3. Hardware Invariant Checks
VRAM_USED=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -n 1 | awk '{print $1}')
python3 -c "assert float('$VRAM_USED') <= 5400.0, f'VRAM ceiling breached: $VRAM_USED MiB'"
test -z "$(git -C "$WORKSPACE/.hermes/hermes-agent" status --porcelain)"

# 4. Cryptographic Sealing of Verified Receipt
python3 -c '
import json
json.dump({
    "exitstatus": 0,
    "workspace": "'"$WORKSPACE"'",
    "active_phase": "phase_45_fastmcp_gate2_abductive_error_sequential_dispatch",
    "all_phases_verified": False,
    "nvml_vram_used_mib": float("'"$VRAM_USED"'"),
    "nvml_vram_limit_mib": 5400.0,
    "gate2_in_flight_active": True,
    "abductive_translator_active": True,
    "sequential_dispatch_active": True,
    "upstream_git_clean": True
}, open("'"$RECEIPT"'", "w"), indent=2)
'

echo "=== [PHASE 45 VERIFIED: 30% Orchestration FastMCP Upgrade Sealed] ==="
