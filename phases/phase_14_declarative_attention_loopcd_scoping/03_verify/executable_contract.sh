#!/usr/bin/env bash
# Verification Contract (V_contract) for Phase 14: Declarative Attention & LoopCD Scoping
set -euo pipefail

distrobox enter ws-hermes -- bash -c 'cd tests/phase14_da_loopcd_eval && PYTHONPATH=".:scenario:scenario/uncertainty_branch" pytest -q'
