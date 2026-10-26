#!/usr/bin/env bash
# Verification Contract (V_contract) for Phase 23: Open-World Replay Simulator Pool (Dream-RSI 2.0)
set -euo pipefail

distrobox enter ws-hermes -- bash -c 'cd tests/phase23_dream_rsi2_eval && PYTHONPATH=".:scenario" pytest -q'
