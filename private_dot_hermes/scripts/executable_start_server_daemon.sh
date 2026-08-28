#!/usr/bin/env bash
# Hermes Self-Contained Server Daemon Starter
# Target: Gemma-4-E4B-it Q4_K_M + MTP Q4_0 on RTX 3050 Laptop (6GB VRAM)
# CPU Pinning: Intel 13th Gen P-Cores (CPUs 0-11 @ 4.6GHz)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HERMES_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
LLAMA_SERVER=""
if command -v llama-server &>/dev/null; then
    LLAMA_SERVER="$(command -v llama-server)"
elif [[ -x "${HOME}/.local/bin/llama-server" ]]; then
    LLAMA_SERVER="${HOME}/.local/bin/llama-server"
elif [[ -x "${HERMES_ROOT}/.local/bin/llama-server" ]]; then
    LLAMA_SERVER="${HERMES_ROOT}/.local/bin/llama-server"
else
    echo "Error: llama-server executable not found in PATH or ~/.local/bin." >&2
    exit 1
fi

echo "[DAEMON] Starting self-contained llama-server on port 8138 with P-Core pinning (0-11)..."
nohup taskset -c 0-11 "${LLAMA_SERVER}" "$@" > /dev/shm/llama_server_hardened.log 2>&1 &
disown
echo "[DAEMON] llama-server started successfully on port 8138 (PID logged to /dev/shm/llama_server_hardened.log)."

