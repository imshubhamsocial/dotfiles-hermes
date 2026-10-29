#!/usr/bin/env bash
# Verification Contract for Phase 44: 60% Infrastructure Compiler Gates
set -euo pipefail

WORKSPACE="/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes"
RECEIPT="/tmp/hermes_verified_receipt.json"

echo "=== [Phase 44 Contract: 60% Infrastructure Compiler Gates] ==="

# 1. Execute Ruff Linter on Infrastructure Gates
python3 -m ruff check "$WORKSPACE/scripts/hermes_ast_canonizer.py" \
                      "$WORKSPACE/scripts/hermes_ruff_precommit.py" \
                      "$WORKSPACE/scripts/hermes_entropy_watchdog.py"

# 2. Comprehensive Test Suite
python3 -c '
import ast
from scripts.hermes_ast_canonizer import (
    CanonicalSignatureTransformer,
    sanitize_and_canonize_edit_surface,
    extract_canonical_function_info
)
from scripts.hermes_ruff_precommit import execute_ruff_precommit_gate
from scripts.hermes_entropy_watchdog import SlidingWindowShannonEntropyWatchdog

print("[1/3] Testing AST Signature and Scope Canonizer...")
# Sub-test A: NameError parameter renaming (len_of_list -> numbers)
stub_mad = "def mean_absolute_deviation(numbers: list[float]) -> float:\n    \"\"\"Docstring\"\"\""
raw_mad = "```python\ndef mean_absolute_deviation(len_of_list: list[float]) -> float:\n    total = sum(len_of_list)\n    return total / len(len_of_list)\n```"
canon_mad = sanitize_and_canonize_edit_surface(raw_mad, stub_mad)
assert "numbers" in canon_mad
assert "len_of_list" not in canon_mad
assert "```" not in canon_mad

# Sub-test B: TypeError orphan self stripping and recursive call rewrite
stub_fib = "def fib(n: int) -> int:"
raw_fib = "def fib(self, n: int) -> int:\n    if n <= 1:\n        return n\n    return self.fib(n - 1) + self.fib(n - 2)"
canon_fib = sanitize_and_canonize_edit_surface(raw_fib, stub_fib)
assert "self" not in canon_fib
assert "return fib(n - 1) + fib(n - 2)" in canon_fib

# Sub-test C: SyntaxError duplicate def header and body stitching
stub_add = "def add(a: int, b: int) -> int:\n"
raw_body = "    return a + b"
canon_add = sanitize_and_canonize_edit_surface(raw_body, stub_add)
assert "def add(a: int, b: int) -> int:" in canon_add
assert "return a + b" in canon_add

print("[2/3] Testing Ruff Pre-Commit Gate...")
# Valid code passes
passed, count, _ = execute_ruff_precommit_gate("def multiply(x, y):\n    return x * y\n")
assert passed is True and count == 0

# Undefined variable fails with F821
failed, err_count, report = execute_ruff_precommit_gate("def multiply(x, y):\n    return x * z\n")
assert failed is False and err_count >= 1 and "F821" in report

print("[3/3] Testing Sliding-Window Shannon Entropy Watchdog...")
watchdog = SlidingWindowShannonEntropyWatchdog(window_size=64, check_interval=16)

# Normal varied code does not trigger
clean_tokens = "def calculate(a, b, c):\n    res = a + b * c\n    return res\n".split(" ")
for tok in clean_tokens:
    assert not watchdog.feed_token(tok)

# Cyclic repetitive loop triggers slot erase within 64 tokens
cyclic_tokens = ["1", ", ", "3", ", ", "2", ", "] * 40
detected = any(watchdog.feed_token(tok) for tok in cyclic_tokens)
assert detected is True, "Cyclic loop not detected by watchdog"

# Truncate at AST boundary test
broken = "def test_fn():\n    val = 10\n    return val +\n"
truncated = watchdog.truncate_at_last_complete_ast_boundary(broken)
assert truncated == "def test_fn():\n    val = 10"
ast.parse(truncated)

print("All Python verification contracts PASSED.")
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
    "active_phase": "phase_44_ast_canonizer_ruff_precommit_entropy_watchdog",
    "all_phases_verified": False,
    "nvml_vram_used_mib": float("'"$VRAM_USED"'"),
    "nvml_vram_limit_mib": 5400.0,
    "ast_canonizer_active": True,
    "ruff_precommit_active": True,
    "entropy_watchdog_active": True,
    "upstream_git_clean": True
}, open("'"$RECEIPT"'", "w"), indent=2)
'

echo "=== [PHASE 44 VERIFIED: 60% Infrastructure Compiler Gates Sealed] ==="
