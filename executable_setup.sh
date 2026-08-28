#!/usr/bin/env bash
set -euo pipefail

echo "==> Configuring DNF for maximum download speed..."
echo 'max_parallel_downloads=20' | sudo tee -a /etc/dnf/dnf.conf > /dev/null

echo "==> Installing base tools & compilers..."
sudo dnf install -y gcc gcc-c++ make cmake clang ripgrep fd-find fzf tree htop nvtop \
    bubblewrap e2fsprogs nodejs22 clang-tools-extra gdb valgrind \
    python3.13 python3.13-devel openssl-devel libffi-devel git git-lfs chezmoi jq curl wget

echo "==> Ensuring pip toolchain & build tools..."
python3.13 -m ensurepip --upgrade
python3.13 -m pip install --break-system-packages setuptools wheel

echo "==> Installing Python & Hermes dependencies..."
python3.13 -m pip install --break-system-packages \
    pytest playwright \
    pydantic pyyaml rich typer httpx openai fastapi uvicorn starlette \
    python-dotenv prompt_toolkit click requests aiohttp websockets \
    uvloop watchfiles cffi cryptography croniter psutil pillow pathspec ruamel.yaml uv \
    fastembed fastmcp mcp mcp-agent-gate mnemory chromadb qdrant-client \
    nvidia-cuda-runtime nvidia-cublas nvidia-cuda-nvrtc nvidia-nccl-cu13

echo "==> Installing Playwright Chromium browser & headless Linux runtime libs..."
sudo dnf install -y alsa-lib libX11 libXcomposite libXdamage libXext libXfixes libXrandr libgbm libxkbcommon pango cairo nss nss-util nspr atk at-spi2-atk dbus-glib libdrm mesa-libgbm cups-libs
python3.13 -m playwright install chromium

echo "==> Installing Node.js CLI tools..."
mkdir -p "$HOME/.local/bin" "$HOME/.local/lib"
npm config set prefix "$HOME/.local"
npm install -g pyright typescript typescript-language-server prettier @ast-grep/cli pnpm \
    bash-language-server dockerfile-language-server-nodejs vscode-langservers-extracted \
    yaml-language-server eslint @biomejs/biome @tobilu/qmd

echo "==> Setting up PATH, environment, and bytecode cache..."
mkdir -p "$HOME/.local/bin" "$HOME/.hermes" "$HOME/.cache/cpython" "$HOME/.cache/huggingface/hub"
if ! grep -q 'PATH=$HOME/.local/bin:$PATH' "$HOME/.bashrc" 2>/dev/null; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
fi
if ! grep -q 'PYTHONPYCACHEPREFIX' "$HOME/.bashrc" 2>/dev/null; then
    echo 'export PYTHONPYCACHEPREFIX="$HOME/.cache/cpython"' >> "$HOME/.bashrc"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "==> Installing hermes-harness package from .hermes/src..."
python3.13 -m pip install --break-system-packages "$SCRIPT_DIR"

echo "==> Setting up official Hermes launcher wrapper..."
cat << 'LAUNCHER' > "$HOME/.local/bin/hermes"
#!/usr/bin/env bash
unset PYTHONPATH
unset PYTHONHOME
export PATH="$HOME/.local/bin:$PATH"
exec python3.13 -m hermes_cli.main "$@"
LAUNCHER
chmod +x "$HOME/.local/bin/hermes"

echo "==> Ensuring SearXNG local keyless web grounding is running..."
CONTAINER_CLI=""
if command -v podman &>/dev/null; then
    CONTAINER_CLI="podman"
elif command -v distrobox-host-exec &>/dev/null && distrobox-host-exec command -v podman &>/dev/null; then
    CONTAINER_CLI="distrobox-host-exec podman"
elif command -v docker &>/dev/null; then
    CONTAINER_CLI="docker"
elif command -v distrobox-host-exec &>/dev/null && distrobox-host-exec command -v docker &>/dev/null; then
    CONTAINER_CLI="distrobox-host-exec docker"
fi

if [[ -n "$CONTAINER_CLI" ]]; then
    if ! curl -s --connect-timeout 2 http://127.0.0.1:8080/ >/dev/null 2>&1; then
        echo "Starting SearXNG container on port 8080..."
        $CONTAINER_CLI start searxng-hermes 2>/dev/null || \
        $CONTAINER_CLI start searxng 2>/dev/null || \
        $CONTAINER_CLI run -d \
            --name searxng-hermes \
            --restart=always \
            -p 8080:8080 \
            docker.io/searxng/searxng:latest || true
    fi
else
    echo "Notice: No container engine found (podman/docker); skipping automatic SearXNG daemon."
fi

echo "==> Verifying champion Gemma-4 GGUF models in standard cache..."
python3.13 -c "
import os
from huggingface_hub import hf_hub_download

hub_dir = os.environ.get('HF_HUB_DIR', os.path.expanduser('~/.cache/huggingface/hub'))
target_dir = os.path.join(hub_dir, 'models--bartowski--gemma-4-E4B-it-GGUF', 'snapshots', 'main')
os.makedirs(target_dir, exist_ok=True)

models = [
    ('gemma-4-E4B-it-Q4_K_M.gguf', 'champion Gemma-4 Q4_K_M model'),
    ('mtp-gemma-4-E4B-it-Q4_0.gguf', 'speculative MTP Q4_0 draft model')
]

for filename, desc in models:
    dest = os.path.join(target_dir, filename)
    if not os.path.exists(dest):
        print(f'==> Downloading {desc} to standard cache...')
        hf_hub_download(
            repo_id='bartowski/gemma-4-E4B-it-GGUF',
            filename=filename,
            local_dir=target_dir
        )
    else:
        print(f'✓ {filename} already present in standard cache.')
"

echo "==> Setting up production hardware-optimized llama-server wrapper..."
cat << 'LLAMA' > "$HOME/.local/bin/llama-server"
#!/usr/bin/env bash
# Hardware-Optimized llama-server Launcher for Gemma-4-E4B-it
# Target GPU: NVIDIA RTX 3050 Laptop (6GB VRAM, <=4,812 MiB safety ceiling)
set -euo pipefail

HERMES_ROOT="${HERMES_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
SITE_PACKAGES="$(python3.13 -m site --user-site 2>/dev/null || echo "${HOME}/.local/lib/python3.13/site-packages")"
LLAMA_LIB_DIR="${HERMES_ROOT}/.hermes/bin/llama"

export LD_LIBRARY_PATH="${LLAMA_LIB_DIR}:${SITE_PACKAGES}/nvidia/cu13/lib:${SITE_PACKAGES}/nvidia/cublas/lib:${SITE_PACKAGES}/nvidia/cuda_nvrtc/lib:${SITE_PACKAGES}/nvidia/nccl/lib:${SITE_PACKAGES}/nvidia/cuda_runtime/lib:${HOME}/.local/share/cuda-libs:${LD_LIBRARY_PATH:-}"

HF_HUB_DIR="${HF_HUB_DIR:-${HOME}/.cache/huggingface/hub}"
MODEL_MAIN="${HF_HUB_DIR}/models--bartowski--gemma-4-E4B-it-GGUF/snapshots/main/gemma-4-E4B-it-Q4_K_M.gguf"
MODEL_DRAFT="${HF_HUB_DIR}/models--bartowski--gemma-4-E4B-it-GGUF/snapshots/main/mtp-gemma-4-E4B-it-Q4_0.gguf"
SERVER_BIN="${HERMES_ROOT}/.hermes/bin/llama/llama-server.bin"

DRAFT_FLAGS=()
if [[ -f "$MODEL_DRAFT" ]]; then
    DRAFT_FLAGS=(
        --model-draft "$MODEL_DRAFT"
        --spec-draft-ngl 99
        --spec-draft-n-max 3
    )
fi

exec "$SERVER_BIN" \
    --model "$MODEL_MAIN" \
    "${DRAFT_FLAGS[@]}" \
    -ngl 99 \
    --flash-attn on \
    --jinja \
    -c 131072 \
    --cache-type-k q4_0 \
    --cache-type-v q4_0 \
    -np 2 \
    --threads 6 \
    --threads-batch 6 \
    --host 127.0.0.1 \
    --port 8138 \
    --metrics \
    --temp 1.0 \
    --top-p 0.95 \
    --top-k 64 \
    "$@"
LLAMA
chmod +x "$HOME/.local/bin/llama-server"

echo "==> Setup complete! All dependencies, models, SearXNG grounding, and wrappers are operational."
