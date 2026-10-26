#!/usr/bin/env bash
# Verification Contract (V_contract) for Phase 12: SoL-Pi Runtime Harness & Two-Strike Tabu
set -euo pipefail

distrobox enter ws-hermes -- bash -c 'cd tests/phase12_sol_pi_eval && PYTHONPATH=".:scenario" pytest -q'
