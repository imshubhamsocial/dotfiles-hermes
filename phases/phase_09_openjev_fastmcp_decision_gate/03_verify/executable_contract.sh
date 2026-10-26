#!/usr/bin/env bash
# Verification Contract (V_contract) for Phase 09: OpenJev FastMCP Decision Gate
set -euo pipefail

distrobox enter ws-hermes -- bash -c 'PYTHONPATH=".:tests/phase27_decision_router_eval" pytest tests/phase27_decision_router_eval/ -q'
