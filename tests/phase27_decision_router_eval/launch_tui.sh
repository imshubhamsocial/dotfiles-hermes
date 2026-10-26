#!/usr/bin/env bash
set -eo pipefail

# Launcher for Phase 27 Level 5 Autonomous Evaluation inside dedicated Konsole GUI window
TESTBED_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$TESTBED_DIR/../.." && pwd)"

export HERMES_HOME="$WORKSPACE_ROOT/.hermes"
export PATH="$WORKSPACE_ROOT/.local/bin:$PATH"

echo "================================================================================"
echo "🚀 HERMES AGENT OS — PHASE 27 SELECTIVE DECISION ROUTER TUI EVALUATION"
echo "================================================================================"
echo "Executing raw, un-spoon-fed prompt inside isolated testbed:"
echo "Prompt: 'Fix the timestamp refill defect in TokenBucketRateLimiter to prevent unauthorized burst on rejected requests'"
echo "--------------------------------------------------------------------------------"

cd "$TESTBED_DIR"

PROMPT="Fix the timestamp refill defect in TokenBucketRateLimiter to prevent unauthorized burst on rejected requests"

# Launch hermes with the raw, natural language prompt (no /goal, no manual constraints)
hermes chat --tui --in "${TESTBED_DIR}" --yolo -q "${PROMPT}"

echo "--------------------------------------------------------------------------------"
echo "🔍 Executing Phase 27 Machine Verification Gate..."
python3 test_verify.py
echo "================================================================================"
echo ""
echo "Execution complete. Press Enter to exit."
read -r
