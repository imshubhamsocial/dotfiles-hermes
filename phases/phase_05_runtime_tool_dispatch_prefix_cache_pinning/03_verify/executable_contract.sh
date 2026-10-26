#!/usr/bin/env bash
# Verification Contract (V_contract) for Phase 05: Runtime Tool Dispatch & Prefix Cache Pinning
set -euo pipefail

distrobox enter ws-hermes -- bash -c 'curl -sf http://127.0.0.1:8138/health | grep -q "\"status\":\"ok\""'
