#!/usr/bin/env bash
set -eo pipefail

TESTBED_DIR="/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes/tests/phase23_dream_rsi2_eval"
cd "${TESTBED_DIR}"

echo "========================================================================"
echo "🚀 Launching Hermes TUI: Phase 23 Dream-RSI 2.0 Replay Simulator Pool"
echo "========================================================================"

PROMPT="/goal Verify and execute the Dream-RSI 2.0 Replay Simulator Pool in tests/phase23_dream_rsi2_eval/scenario/replay_simulator.py, asserting content-addressed replay tree persistence, Doubly Robust off-policy value estimation, RRSI variance stability gating (Delta >= k * sigma_0), and call reduction ratio >= 2.0x.

outcome:
  1. Inspect tests/phase23_dream_rsi2_eval/scenario/replay_simulator.py.
  2. Persist execution trajectories into content-addressed JSON replay trees.
  3. Execute Doubly Robust counterfactual policy evaluation on CPU RAM (latency <= 50.0 ms).
  4. Validate RRSI stability gate compliance rejecting high-variance spurious mutations.
  5. Assert call reduction ratio >= 2.0x and 0 MiB CUDA VRAM delta.
  6. All tests in tests/phase23_dream_rsi2_eval/ pass with exit code 0.

verify: pytest tests/phase23_dream_rsi2_eval/ -q"

# Launch Hermes TUI in the testbed
hermes chat --tui --in "${TESTBED_DIR}" --yolo -q "${PROMPT}"

echo ""
echo "========================================================================"
echo "🔍 Running Deterministic Verification Gate..."
echo "========================================================================"
./run_eval.sh

echo ""
echo "Execution complete. Press Enter to exit."
read -r
