#!/usr/bin/env bash
# Verification Contract (V_contract) for Phase 18: Embodied Visual World Model (SmolVLM2 \+ AT-SPI2)
set -euo pipefail

distrobox enter ws-hermes -- bash -c 'cd tests/phase18_arc_agui_eval && PYTHONPATH=".:scenario" pytest -q'
