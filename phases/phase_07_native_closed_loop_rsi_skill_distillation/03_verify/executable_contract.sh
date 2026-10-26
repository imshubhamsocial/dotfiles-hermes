#!/usr/bin/env bash
# Verification Contract (V_contract) for Phase 07: Native Closed-Loop RSI Skill Distillation
set -euo pipefail

distrobox enter ws-hermes -- bash -c 'PYTHONPATH=".:tests/phase16_dream_rsi_eval" pytest tests/phase16_dream_rsi_eval/ -q'
