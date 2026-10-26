#!/usr/bin/env bash
# Verification Contract (V_contract) for Phase 17: Hibernate-and-Train LoGRA/NoRA \+ GrowMTP
set -euo pipefail

distrobox enter ws-hermes -- bash -c 'cd tests/phase17_logra_nora_eval && PYTHONPATH=".:scenario" pytest -q'
