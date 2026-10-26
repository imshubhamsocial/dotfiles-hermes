#!/usr/bin/env bash
# Verification Contract (V_contract) for Phase 06: Pydantic v2 Settings & Schema Migration
set -euo pipefail

distrobox enter ws-hermes -- pytest tests/phase01_canonical_parity/test_phase01_parity.py -k test_pydantic_v2_path_sanitization -q
