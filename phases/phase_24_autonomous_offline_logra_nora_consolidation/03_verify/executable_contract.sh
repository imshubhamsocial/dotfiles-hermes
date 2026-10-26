#!/usr/bin/env bash
# Verification Contract (V_contract) for Phase 24: Autonomous Offline LoGRA/NoRA Consolidation
set -euo pipefail

distrobox enter ws-hermes -- bash -c 'cd tests/phase24_autonomous_logra_eval && PYTHONPATH=".:scenario" pytest -q'
