#!/usr/bin/env bash
set -euo pipefail

SKILL_PATH="$HOME/.hermes/skills/domain_db_tool_precedence/SKILL.md"
RECEIPT_FILE="/tmp/hermes_verified_receipt.json"

test -f "$SKILL_PATH"

# Verify structural sections exist
grep -q "name: domain_db_tool_precedence" "$SKILL_PATH"
grep -q "## 1. Core Epistemic Principle (The Exhaustion Invariant)" "$SKILL_PATH"
grep -q "## 2. Pre-Escalation Decision Protocol" "$SKILL_PATH"

# Zero contamination assertion gate
! grep -Ei "isabella|johansson|32286|w4284542|hernandez|92133|clara|vance" "$SKILL_PATH"

python3 -c '
import json
json.dump({
    "exitstatus": 0,
    "phase": "phase_35",
    "verified": True,
    "skill_path": "'"$SKILL_PATH"'"
}, open("'"$RECEIPT_FILE"'", "w"))
'
echo "PHASE 35 VERIFIED: Domain DB Tool Precedence skill deployed."
