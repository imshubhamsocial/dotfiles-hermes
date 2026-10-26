#!/usr/bin/env bash
# Verification Contract (V_contract) for Phase 15: Proactive Security Gate & SymPy VRAM Proof
set -euo pipefail

distrobox enter ws-hermes -- bash -c 'cd tests/phase15_regen_security_eval && PYTHONPATH=".:scenario" pytest -q'
