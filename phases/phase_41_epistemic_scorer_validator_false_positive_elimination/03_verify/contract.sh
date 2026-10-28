#!/usr/bin/env bash
# Verification Contract for Phase 41: Epistemic Scorer Validator & False-Positive Elimination
set -euo pipefail

WORKSPACE="/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes"
VALIDATOR="/var/home/imshubhamsocial/Desktop/GDR/GDR24/verify_epistemic_eval_audit.py"
RECEIPT="/tmp/hermes_verified_receipt.json"

chmod +x "$VALIDATOR"
python3 -m py_compile "$VALIDATOR"

python3 -c '
import sys
sys.path.insert(0, "/var/home/imshubhamsocial/Desktop/GDR/GDR24")
import verify_epistemic_eval_audit as v

# Test 1: GDR24 Sample 105 Role-Rejection Transcript MUST be flagged as False-Positive
sample_105_bad = [
    {"role": "user", "content": "Hello, I am calling about order #W4316152. My name is Aarav Anderson and zip is 19031."},
    {"role": "assistant", "content": "I apologize for the confusion. As an AI assistant, I do not operate a physical online store or have access to private customer databases."}
]
res_bad = v.audit_sample_messages("105", sample_105_bad, "C")
assert res_bad["naive_pass"] is True
assert res_bad["g_persona_pass"] is False
assert res_bad["g_read_pass"] is False
assert res_bad["epistemic_validated_pass"] is False
assert res_bad["false_positive_detected"] is True, "Failed to catch Sample 105 false positive!"

# Test 2: Remediated Read-Verified Policy Execution MUST pass all 3 Epistemic Gates
sample_105_good = [
    {"role": "user", "content": "Hello, I am calling about order #W4316152. My name is Aarav Anderson and zip is 19031."},
    {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {"id": "call_1", "type": "function", "function": {"name": "find_user_id_by_name_zip", "arguments": "{\"first_name\":\"Aarav\",\"last_name\":\"Anderson\",\"zip\":\"19031\"}"}},
            {"id": "call_2", "type": "function", "function": {"name": "get_order_details", "arguments": "{\"order_id\":\"#W4316152\"}"}}
        ]
    },
    {"role": "tool", "tool_call_id": "call_1", "content": "aarav_anderson_8812"},
    {"role": "tool", "tool_call_id": "call_2", "content": "{\"order_id\":\"#W4316152\",\"status\":\"delivered\"}"},
    {"role": "assistant", "content": "I have located your profile (aarav_anderson_8812) and inspected order #W4316152. Per store policy, I will now process the verified steps or transfer as required."}
]
res_good = v.audit_sample_messages("105_remediated", sample_105_good, "C")
assert res_good["g_persona_pass"] is True
assert res_good["g_read_pass"] is True
assert res_good["g_isolation_pass"] is True
assert res_good["epistemic_validated_pass"] is True
assert res_good["false_positive_detected"] is False
'

test -z "$(git -C "$WORKSPACE/.hermes/hermes-agent" status --porcelain)"

python3 -c '
import json
json.dump({
    "exitstatus": 0,
    "workspace": "'"$WORKSPACE"'",
    "phase": "phase_41_epistemic_scorer_validator_false_positive_elimination",
    "sample_105_false_positive_caught": True,
    "upstream_git_clean": True
}, open("'"$RECEIPT"'", "w"), indent=2)
'
echo "PHASE 41 VERIFIED: 3-Gate Epistemic Validator eliminates Sample 105 false positives."
