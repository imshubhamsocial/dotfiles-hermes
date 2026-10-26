#!/usr/bin/env bash
set -eo pipefail

TESTBED_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${TESTBED_DIR}"

echo "========================================================================"
echo "🚀 Launching Hermes TUI: Phase 24 Offline LoGRA/NoRA Weight Evolution"
echo "========================================================================"

PROMPT="/goal Execute and verify Autonomous Offline LoGRA/NoRA Weight Evolution in scenario/offline_adapter_engine.py, asserting Temporal Mutual Exclusion (TME), VRAM quorum <= 650 MiB, peak VRAM <= 4812 MiB, rank-64 LoGRA gradient sketches, NoRA Frobenius normalization ||A||_F == 1.0, and post-resume MTP draft throughput >= 42.4 tok/s.

outcome:
  1. Inspect scenario/offline_adapter_engine.py and scenario/training_buffer/samples.jsonl.
  2. Verify VRAMQuorumGuard enforces temporal mutual exclusion and prevents VRAM over-allocation.
  3. Validate rank-64 LoGRA gradient sketching eliminating dense optimizer buffers.
  4. Assert NoRA down-projection Frobenius normalization ||A||_F == 1.0.
  5. Assert post-consolidation KL divergence <= 0.05.
  6. Assert post-resume Port 8138 MTP throughput >= 42.4 tok/s.
  7. All tests in . pass with exit code 0.

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
