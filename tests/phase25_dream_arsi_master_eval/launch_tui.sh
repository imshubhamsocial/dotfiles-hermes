#!/usr/bin/env bash
set -eo pipefail

TESTBED_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${TESTBED_DIR}"

echo "========================================================================"
echo "🚀 Launching Hermes TUI: Phase 25 Dream-ARSI Master Omniscient Parity"
echo "========================================================================"

PROMPT="/goal Execute and verify Dream-ARSI Master Omniscient Parity in scenario/arsi_kernel.py, proving complete 6-Challenge Argon Gauntlet mastery, VRAM budget <= 4812 MiB, 0 MiB CUDA AST outline navigation, declarative attention attractor convergence, Kahn's TaskDAG resolution with 0 circular deadlocks, Spec-Kit 2.0 clean-slate failure annealing (Dt+1 = 0), and Dream-RSI 2.0 TME quorum.

outcome:
  1. Inspect scenario/arsi_kernel.py.
  2. Verify Challenge 1: STAIR AST navigation executes on CPU RAM with 0 MiB CUDA memory delta.
  3. Verify Challenge 2: Declarative Attention and Latent Thought Attractors converge within 5 iterations with >= 85% KV reuse.
  4. Verify Challenge 3: Proactive Security Gate neutralizes 100% prompt injections and SymPy proves VRAM <= 4812.0 MiB.
  5. Verify Challenge 4: Google ADK TaskDAG resolves 4 subagent personas with 0 circular deadlocks.
  6. Verify Challenge 5: Spec-Kit 2.0 failure cluster annealing eliminates residual debt (Dt+1 = 0).
  7. Verify Challenge 6: Dream-RSI 2.0 simulator pool reduces live calls >= 2.0x and enforces TME (<= 650 MiB, ||A||_F == 1.0).
  8. All tests in . pass with exit code 0.

verify: pytest . -q"

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
