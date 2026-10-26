#!/usr/bin/env bash
# Verification Contract (V_contract) for Phase 11: Polyglot Compiler & Linter Verification Gate
set -euo pipefail

distrobox enter ws-hermes -- ruff check .hermes/mcp_openjev.py conftest.py
