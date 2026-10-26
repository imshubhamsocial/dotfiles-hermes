#!/usr/bin/env bash
# Verification Contract (V_contract) for Phase 27: Two-Stage Zero-Eviction Decision Router
set -euo pipefail

distrobox enter ws-hermes -- bash -c 'cd tests/phase27_decision_router_eval && PYTHONPATH=".:scenario" pytest -q'
