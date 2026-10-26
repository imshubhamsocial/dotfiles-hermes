#!/usr/bin/env bash
# Verification Contract (V_contract) for Phase 03: Ebbinghaus Memory Forgetting & Spillover Gate
set -euo pipefail

CMD='python3 -c "from pathlib import Path; m = Path(\".hermes/memories/MEMORY.md\").read_text(); assert len(m) <= 2200 and \"§1\" in m"'

if command -v distrobox >/dev/null 2>&1; then
    distrobox enter ws-hermes -- bash -c "$CMD"
else
    bash -c "$CMD"
fi
