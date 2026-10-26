#!/usr/bin/env bash
# Verification Contract (V_contract) for Phase 19: Banach Fixed-Point Latent Deliberator
set -euo pipefail

distrobox enter ws-hermes -- bash -c 'cd tests/phase19_looped_attractor_eval && PYTHONPATH=".:scenario" pytest -q'
