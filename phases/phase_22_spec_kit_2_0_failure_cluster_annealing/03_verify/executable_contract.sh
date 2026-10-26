#!/usr/bin/env bash
# Verification Contract (V_contract) for Phase 22: Spec-Kit 2.0 Failure Cluster Annealing
set -euo pipefail

distrobox enter ws-hermes -- bash -c 'cd tests/phase22_speckit_annealing_eval && PYTHONPATH=".:scenario" pytest -q'
