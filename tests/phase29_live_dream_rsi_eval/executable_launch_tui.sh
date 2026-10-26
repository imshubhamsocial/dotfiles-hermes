#!/usr/bin/env bash
set -eo pipefail

# Launcher for Phase 29 Level 5 Autonomous Evaluation inside dedicated Konsole GUI window
TESTBED_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$TESTBED_DIR/../.." && pwd)"

export HERMES_HOME="$WORKSPACE_ROOT/.hermes"
export PATH="$WORKSPACE_ROOT/.local/bin:$PATH"

echo "================================================================================"
echo "🚀 HERMES AGENT OS — PHASE 29 LIVE STATE.DB DREAM-RSI 2.0 TUI EVALUATION"
echo "================================================================================"
echo "Executing raw, un-spoon-fed prompt inside isolated testbed:"
echo "Prompt: 'Fix the IndexError in LiveDreamSyncEngine (scenario/live_sync.py) when building replay tree dictionaries from state.db session records'"
echo "--------------------------------------------------------------------------------"

cd "$TESTBED_DIR"

PROMPT="Fix the IndexError in LiveDreamSyncEngine (scenario/live_sync.py) when building replay tree dictionaries from state.db session records"

# Launch hermes with the raw, natural language prompt (no /goal, no manual constraints)
hermes chat --tui --in "${TESTBED_DIR}" --yolo -q "${PROMPT}"

echo "--------------------------------------------------------------------------------"
echo "🔍 Executing Phase 29 Machine Verification Gate..."
python3 test_verify.py
echo "================================================================================"
echo ""
echo "Execution complete. Press Enter to exit."
read -r
