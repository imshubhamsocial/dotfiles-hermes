#!/usr/bin/env bash
# Verification Contract (V_contract) for Phase 02: OpenViking Hierarchical Memory Server
set -euo pipefail

CMD='curl -sf http://127.0.0.1:1933/health | grep -q "\"healthy\":true"'

if command -v distrobox >/dev/null 2>&1; then
    distrobox enter ws-hermes -- bash -c "$CMD"
else
    bash -c "$CMD"
fi
