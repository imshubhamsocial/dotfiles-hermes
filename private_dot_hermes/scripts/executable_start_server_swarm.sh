#!/usr/bin/env bash
# Hermes Server Swarm Starter (N=4 Slots, 103+ tok/s aggregate)
# Target: Headless swarm benchmarks and multi-subagent batch processing
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HERMES_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LLAMA_SERVER="${HERMES_ROOT}/.local/bin/llama-server"

echo "[SWARM] Starting llama-server with 4 parallel slots and P-Core pinning (0-11)..."
nohup taskset -c 0-11 "${LLAMA_SERVER}" -np 4 --parallel 4 "$@" > /dev/shm/llama_server_swarm.log 2>&1 &
disown
echo "[SWARM] llama-server swarm mode started successfully."
