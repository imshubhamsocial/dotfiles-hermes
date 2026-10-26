#!/usr/bin/env bash
# Verification Contract (V_contract) for Phase 04: Two-Tier Progressive Skill Catalog
set -euo pipefail

distrobox enter ws-hermes -- python3 -c 'import glob; skills = glob.glob(".hermes/skills/*/SKILL.md"); assert len(skills) >= 14'
