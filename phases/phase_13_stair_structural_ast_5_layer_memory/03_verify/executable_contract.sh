#!/usr/bin/env bash
# Verification Contract (V_contract) for Phase 13: STAIR Structural AST & 5-Layer Memory
set -euo pipefail

distrobox enter ws-hermes -- bash -c 'cd tests/phase13_stair_memory_eval && PYTHONPATH=".:scenario:scenario/polyglot_repo" pytest -q'
