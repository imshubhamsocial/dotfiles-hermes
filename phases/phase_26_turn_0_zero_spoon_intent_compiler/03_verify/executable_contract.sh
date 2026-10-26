#!/usr/bin/env bash
# Verification Contract (V_contract) for Phase 26: Turn-0 Zero-Spoon Intent Compiler
set -euo pipefail

distrobox enter ws-hermes -- bash -c 'cd tests/phase26_zero_spoon_eval && PYTHONPATH=".:scenario" pytest -q'
