#!/usr/bin/env bash
# Verification Contract (V_contract) for Phase 20: Google Harness² Continuous RSI Meta-Loop
set -euo pipefail

distrobox enter ws-hermes -- bash -c 'cd tests/phase20_continuous_rsi_eval && PYTHONPATH=".:scenario" pytest -q'

#### **Tier 3: Declarative Tool Schemas & Execution Sandboxing (Phases 21–25)**
