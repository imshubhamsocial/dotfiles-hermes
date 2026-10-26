#!/usr/bin/env bash
# Verification Contract (V_contract) for Phase 32: Asymmetric Attention & Production AGI Gauntlet
set -euo pipefail

distrobox enter ws-hermes -- bash -c 'for p in tests/phase{12..30}*; do (cd "$p" && PYTHONPATH=".:scenario:scenario/polyglot_repo:scenario/uncertainty_branch" pytest -q); done'
