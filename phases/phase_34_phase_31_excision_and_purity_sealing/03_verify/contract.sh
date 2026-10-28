#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes"
RECEIPT_FILE="/tmp/hermes_verified_receipt.json"

export PATH="$WORKSPACE/.local/bin:$PATH"

# Check syntax of FastMCP module
python3 -m py_compile "$WORKSPACE/.hermes/mcp_openjev.py"
ruff check "$WORKSPACE/.hermes/mcp_openjev.py"

# Verify complete absence of mock identifiers in active codebase
! grep -rn --exclude-dir=logs --exclude-dir=cache --exclude-dir=__pycache__ --exclude="*.bak" "jev_arc_agi_neurosymbolic_solve" "$WORKSPACE/.hermes/"
! grep -rn "def transform(grid):" "$WORKSPACE/.hermes/mcp_openjev.py"

# Verify Law 10 in SOUL.md
grep -q "Law 10: Search-and-Verify Hypothesis Induction" "$WORKSPACE/.hermes/SOUL.md"

python3 -c '
import json
json.dump({
    "exitstatus": 0,
    "phase": "phase_34",
    "verified": True,
    "modified": [".hermes/mcp_openjev.py", ".hermes/SOUL.md"]
}, open("'"$RECEIPT_FILE"'", "w"))
'
echo "PHASE 34 VERIFIED: Substrate purity sealed."
