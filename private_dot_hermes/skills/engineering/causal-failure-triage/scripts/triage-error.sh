#!/usr/bin/env bash
# Quick regex scan to help classify an error trace into 4 quadrants
set -euo pipefail

LOG_TRACE="${1:-}"
if [ -z "$LOG_TRACE" ]; then
    echo "Usage: $0 <error-message>" >&2
    exit 1
fi

if echo "$LOG_TRACE" | grep -qiE "not found|no such file|command not found|permission denied|eacces"; then
    echo "Classification: QUADRANT III (Environment Defect / Substrate Reconnaissance Needed)"
elif echo "$LOG_TRACE" | grep -qiE "importerror|nameerror|attributeerror|nosuchsymbol"; then
    echo "Classification: QUADRANT II (Grounding Error / Symbol Index Query Needed)"
elif echo "$LOG_TRACE" | grep -qiE "assertionerror|valueerror|typeerror|contract"; then
    echo "Classification: QUADRANT IV (Logic/Regression Error / Tabu Swap + Dialectic Critique Needed)"
else
    echo "Classification: QUADRANT I (Spec Ambiguity / Inspect Specification DAG)"
fi
