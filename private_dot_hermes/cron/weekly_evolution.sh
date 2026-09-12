#!/usr/bin/env bash
# Hermes Agent OS — Weekly Self-Evolution Automation (Milestone 53)
# Scheduled to run every Sunday at 02:00 UTC
set -euo pipefail

HERMES_BIN="${HOME}/.local/bin/hermes"
EVOLUTION_DIR="${HOME}/.hermes/memories/evolution"
[[ -d "${EVOLUTION_DIR}" ]] || EVOLUTION_DIR="${HOME}/.hermes/evolution"
mkdir -p "${EVOLUTION_DIR}/baselines" "${EVOLUTION_DIR}/hypotheses"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BASELINE_FILE="${EVOLUTION_DIR}/baselines/baseline_${TIMESTAMP}.json"

echo "[Weekly Evolution] Running automated skill benchmark and failure audit..."
"${HERMES_BIN}" exam > /dev/null
"${HERMES_BIN}" evolve analyze > "${EVOLUTION_DIR}/failure_analysis_${TIMESTAMP}.txt"
"${HERMES_BIN}" evolve propose --top 3
echo "[Weekly Evolution] Audit cycle complete. Baseline and hypotheses recorded."
