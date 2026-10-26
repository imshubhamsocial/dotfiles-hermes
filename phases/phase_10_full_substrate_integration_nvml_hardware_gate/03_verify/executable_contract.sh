#!/usr/bin/env bash
# Verification Contract (V_contract) for Phase 10: Full Substrate Integration & NVML Hardware Gate
set -euo pipefail

distrobox enter ws-hermes -- python3 -c 'import sys; sys.path.insert(0, ".hermes"); import mcp_openjev as m; v = m.query_live_nvml_vram(); assert v["used_mib"] <= 5400.0'

#### **Tier 2: Cognitive Deliberation & Memory Architecture (Phases 11–20)**
