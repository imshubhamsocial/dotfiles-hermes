#!/usr/bin/env bash
# Hardware-Optimized Multimodal Vision Sidecar Server (Port 8139)
# Model: SmolVLM2-256M-Video-Instruct-Q4_K_M.gguf + mmproj-Q8_0.gguf
# Target: 100% CPU inference (-ngl 0) to strictly preserve GPU VRAM (0 MB VRAM overhead)
set -euo pipefail

HERMES_ROOT="${HERMES_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
SITE_PACKAGES="$(python3 -m site --user-site 2>/dev/null || echo "${HOME}/.local/lib/python3.14/site-packages")"
LLAMA_LIB_DIR="/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes/.local/lib"

export LD_LIBRARY_PATH="${LLAMA_LIB_DIR}:${SITE_PACKAGES}/nvidia/cu13/lib:${SITE_PACKAGES}/nvidia/cublas/lib:${SITE_PACKAGES}/nvidia/cuda_nvrtc/lib:${SITE_PACKAGES}/nvidia/nccl/lib:${SITE_PACKAGES}/nvidia/cuda_runtime/lib:/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes/.local/lib/python3.13/site-packages/nvidia/cu13/lib:/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes/.local/lib/python3.13/site-packages/nvidia/cublas/lib:/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes/.local/lib/python3.13/site-packages/nvidia/cuda_runtime/lib:${HOME}/.local/share/cuda-libs:${LD_LIBRARY_PATH:-}"

SERVER_BIN="/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes/.local/bin/llama-server.bin"
if [[ ! -x "$SERVER_BIN" ]]; then
    SERVER_BIN="${HOME}/.local/bin/llama-server.bin"
fi

MODEL_DIR="${HERMES_ROOT}/models/vision"
MODEL_MAIN="${MODEL_DIR}/SmolVLM2-256M-Video-Instruct-Q4_K_M.gguf"
MODEL_MMPROJ="${MODEL_DIR}/mmproj-SmolVLM2-256M-Video-Instruct-Q8_0.gguf"

PID_FILE="/dev/shm/hermes_vision_server.pid"
LOG_FILE="/dev/shm/hermes_vision_server.log"

case "${1:-start}" in
    start)
        if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
            echo "Vision server already running (PID: $(cat "$PID_FILE"))"
            exit 0
        fi
        setsid "$SERVER_BIN" \
            --model "$MODEL_MAIN" \
            --mmproj "$MODEL_MMPROJ" \
            --port 8139 \
            --host 127.0.0.1 \
            -ngl 0 \
            --threads 4 \
            --threads-batch 4 \
            -c 4096 \
            > "$LOG_FILE" 2>&1 &
        SERVER_PID=$!
        echo "$SERVER_PID" > "$PID_FILE"
        echo "Vision server started with PID $SERVER_PID"
        ;;
    stop)
        if [[ -f "$PID_FILE" ]]; then
            PID=$(cat "$PID_FILE")
            echo "Stopping Vision server (PID: $PID)..."
            kill -15 "$PID" 2>/dev/null || true
            rm -f "$PID_FILE"
        else
            echo "Vision server not running."
        fi
        ;;
    status)
        if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
            echo "Vision server RUNNING (PID: $(cat "$PID_FILE"))"
        else
            echo "Vision server STOPPED"
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|status}"
        exit 1
        ;;
esac
