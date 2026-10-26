#!/usr/bin/env bash
# Verification Contract (V_contract) for Phase 16: Dream-RSI Replay Simulator & MASS Loop
set -euo pipefail

distrobox enter ws-hermes -- bash -c 'cd tests/phase16_dream_rsi_eval && PYTHONPATH=".:scenario" pytest -q'
