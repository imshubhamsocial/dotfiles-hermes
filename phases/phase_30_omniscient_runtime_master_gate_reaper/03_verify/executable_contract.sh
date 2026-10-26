#!/usr/bin/env bash
# Verification Contract (V_contract) for Phase 30: Omniscient Runtime Master Gate & Reaper
set -euo pipefail

distrobox enter ws-hermes -- bash -c 'cd tests/phase30_master_runtime_eval && PYTHONPATH=".:scenario" pytest -q'
