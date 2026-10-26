#!/usr/bin/env bash
set -e

# Launcher for Phase 26 Level 5 Autonomous Evaluation inside dedicated Konsole GUI window
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

export HERMES_HOME="$WORKSPACE_ROOT/.hermes"
export PATH="$WORKSPACE_ROOT/.local/bin:$PATH"

echo "================================================================================"
echo "HERMES AGENT OS — PHASE 26 ZERO-SPOON-FEEDING INTENT COMPILER TUI EVALUATION"
echo "================================================================================"
echo "Executing raw, un-spoon-fed prompt inside isolated testbed:"
echo "Prompt: 'Fix the KeyError in DataPipeline when processing legacy telemetry records'"
echo "--------------------------------------------------------------------------------"

cd "$SCRIPT_DIR"

# Launch hermes with the raw, natural language prompt (no /goal, no manual constraints)
hermes --in "$SCRIPT_DIR" "Fix the KeyError in DataPipeline when processing legacy telemetry records"

echo "--------------------------------------------------------------------------------"
echo "Executing Phase 26 Machine Verification Gate..."
python3 test_verify.py
echo "================================================================================"
