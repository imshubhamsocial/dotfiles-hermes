#!/usr/bin/env bash
set -eo pipefail

# Launcher for Phase 30 Level 5 Autonomous Evaluation inside dedicated Konsole GUI window
TESTBED_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$TESTBED_DIR/../.." && pwd)"

export HERMES_HOME="$WORKSPACE_ROOT/.hermes"
export PATH="$WORKSPACE_ROOT/.local/bin:$PATH"

echo "================================================================================"
echo "🚀 HERMES AGENT OS — PHASE 30 OMNISCIENT MASTER RUNTIME TUI EVALUATION"
echo "================================================================================"
echo "Executing raw, un-spoon-fed prompt inside isolated testbed:"
echo "Prompt: 'Fix the ValueError in OmniscientKernelVerifier (scenario/live_omniscient.py) where VRAM ceiling validation fails against live NVML allocation'"
echo "--------------------------------------------------------------------------------"

cd "$TESTBED_DIR"

PROMPT="Fix the ValueError in OmniscientKernelVerifier (scenario/live_omniscient.py) where VRAM ceiling validation fails against live NVML allocation"

# Launch hermes with the raw, natural language prompt (no /goal, no manual constraints)
hermes chat --tui --in "${TESTBED_DIR}" --yolo -q "${PROMPT}"

echo "--------------------------------------------------------------------------------"
echo "🔍 Executing Phase 30 Machine Verification Gate..."
python3 test_verify.py
echo "================================================================================"
echo ""
echo "Execution complete. Press Enter to exit."
read -r
