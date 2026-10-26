#!/usr/bin/env bash
# Verification Contract (V_contract) for Phase 29: Live state.db SQLite WAL Dream-RSI Sync
set -euo pipefail

distrobox enter ws-hermes -- bash -c 'cd tests/phase29_live_dream_rsi_eval && PYTHONPATH=".:scenario" pytest -q'
