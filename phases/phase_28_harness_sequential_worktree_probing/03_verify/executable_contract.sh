#!/usr/bin/env bash
# Verification Contract (V_contract) for Phase 28: Harness² Sequential Worktree Probing
set -euo pipefail

distrobox enter ws-hermes -- bash -c 'cd tests/phase28_harness2_worktree_eval && PYTHONPATH=".:scenario" pytest -q'
