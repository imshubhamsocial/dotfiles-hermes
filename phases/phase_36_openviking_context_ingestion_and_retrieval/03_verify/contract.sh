#!/usr/bin/env bash
set -euo pipefail

RECEIPT_FILE="/tmp/hermes_verified_receipt.json"

# 1. Verify OpenViking daemon health
curl -sf http://127.0.0.1:1933/health > /dev/null

# 2. Query search endpoint to verify retrieval
python3 -c '
import urllib.request, json
req = urllib.request.Request(
    "http://127.0.0.1:1933/api/v1/search/search",
    data=json.dumps({"query": "precedence", "target_uri": "viking://user/default/memories/skills"}).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req, timeout=5.0) as resp:
    res = json.loads(resp.read().decode("utf-8"))
    assert res.get("status") == "ok"
    assert len(res["result"]["memories"]) > 0
    assert "domain_db_tool_precedence" in res["result"]["memories"][0]["uri"]
'

# 3. Verify golden snapshot exists
test -d "$HOME/.openviking/data.golden_clean"

python3 -c '
import json
json.dump({
    "exitstatus": 0,
    "phase": "phase_36",
    "verified": True,
    "openviking_port": 1933,
    "golden_snapshot": True
}, open("'"$RECEIPT_FILE"'", "w"))
'
echo "PHASE 36 VERIFIED: OpenViking L0/L1/L2 tiered context operational."
