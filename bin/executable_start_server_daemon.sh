#!/usr/bin/env bash
# Hermes Self-Contained Server Daemon Starter
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HERMES_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LLAMA_SERVER="${HERMES_ROOT}/.local/bin/llama-server"

echo "[DAEMON] Starting self-contained llama-server on port 8138..."
nohup "${LLAMA_SERVER}" "$@" > /dev/shm/llama_server_hardened.log 2>&1 &
disown
echo "[DAEMON] llama-server started successfully."
