#!/usr/bin/env bash
# Verification Contract for Phase 46: Zero-VRAM Disk-KV MCTS Engine
set -euo pipefail

WORKSPACE="/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes"
RECEIPT="/tmp/hermes_verified_receipt.json"

echo "=== [Phase 46 Contract: Zero-VRAM Disk-KV MCTS Engine] ==="

# 1. Execute Ruff Linter on MCTS Module
python3 -m ruff check "$WORKSPACE/scripts/hermes_disk_kv_mcts.py"

# 2. Comprehensive Test Suite
python3 -c '
from scripts.hermes_disk_kv_mcts import DiskKVMCTSEngine, compute_deterministic_value

print("[1/2] Testing Deterministic Value Function V_det...")
# Case 1: Perfect pass (AST valid, 0 ruff errors, 100% tests, Gate2 pass)
v_max = compute_deterministic_value(True, 0, 1.0, True)
assert v_max == 1.0, f"Expected 1.0, got {v_max}"

# Case 2: Partial pass (AST valid, 1 ruff error, 50% tests, Gate2 pass)
v_mid = compute_deterministic_value(True, 1, 0.5, True)
assert 0.65 <= v_mid <= 0.75, f"Unexpected mid score: {v_mid}"

# Case 3: Syntax error (AST invalid, 0% tests)
v_fail = compute_deterministic_value(False, 2, 0.0, True)
assert v_fail <= 0.30, f"Unexpected fail score: {v_fail}"

print("[2/2] Testing Disk-KV Time-Multiplexed MCTS Search...")
engine = DiskKVMCTSEngine(kv_dir="/tmp/hermes_mcts_test_kv")

prompt_stub = "def multiply_list(numbers: list[int]) -> int:\n    \"\"\"Multiply elements\"\"\""

def generate_actions(code):
    return [
        ("```python\ndef multiply_list(items: list[int]) -> int:\n    res = 1\n    for x in items:\n        res *= x\n    return res\n```", 0.5), # Correct logic + renamed param + fences
        ("def multiply_list(numbers: list[int]) -> int:\n    return 0", 0.3),                                                            # Incorrect logic
        ("def multiply_list(numbers: list[int]) -> int:\n    return", 0.2),                                                               # Syntax error
    ]

def evaluate_test(code):
    loc = {}
    exec(code, {}, loc)
    fn = loc["multiply_list"]
    assert fn([2, 3, 4]) == 24
    assert fn([]) == 1
    return 1.0

best_node = engine.run_mcts_search(
    root_code="",
    candidates_generator=generate_actions,
    prompt_stub=prompt_stub,
    test_fn=evaluate_test,
    iterations=3
)

assert best_node.deterministic_value == 1.0, f"Expected 1.0, got {best_node.deterministic_value}"
assert "for x in numbers:" in best_node.action_code
assert engine.save_count >= 1
assert engine.restore_count >= 1

print("All Disk-KV MCTS verification contracts PASSED.")
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
    "active_phase": "phase_46_disk_kv_mcts_engine_swa_full_dev_shm",
    "all_phases_verified": False,
    "nvml_vram_used_mib": float("'"$VRAM_USED"'"),
    "nvml_vram_limit_mib": 5400.0,
    "disk_kv_mcts_active": True,
    "deterministic_v_det_active": True,
    "upstream_git_clean": True
}, open("'"$RECEIPT"'", "w"), indent=2)
'

echo "=== [PHASE 46 VERIFIED: Zero-VRAM Disk-KV MCTS Engine Sealed] ==="
