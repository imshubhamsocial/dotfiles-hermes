#!/usr/bin/env bash
# Verification Contract (V_contract) for Phase 01: Canonical Upstream Parity & Zero-Bespoke Core
set -euo pipefail

CMD='test -z "$(git -C ~/.hermes/hermes-agent status --porcelain)" && test -z "$(chezmoi unmanaged ~/.hermes)" && pytest tests/phase01_canonical_parity/ -q'

if command -v distrobox >/dev/null 2>&1; then
    distrobox enter ws-hermes -- bash -c "$CMD"
else
    bash -c "$CMD"
fi
