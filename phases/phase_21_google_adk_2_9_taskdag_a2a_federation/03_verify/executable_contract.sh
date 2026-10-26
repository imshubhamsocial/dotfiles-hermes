#!/usr/bin/env bash
# Verification Contract (V_contract) for Phase 21: Google ADK 2.9+ TaskDAG & A2A Federation
set -euo pipefail

distrobox enter ws-hermes -- bash -c 'cd tests/phase21_adk_taskdag_eval && PYTHONPATH=".:scenario" pytest -q'
