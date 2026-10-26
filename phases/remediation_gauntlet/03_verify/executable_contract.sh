#!/usr/bin/env bash
# Verification Contract (V_contract) for Post-Certification Remediation Gauntlet
set -euo pipefail

distrobox enter ws-hermes -- bash -c 'cd /var/home/imshubhamsocial/Projects/Workspace/Personal/hermes/tests/remediation_eval && PYTHONPATH=".:scenario" pytest -q'
