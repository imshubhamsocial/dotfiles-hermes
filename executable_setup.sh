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

echo "==> Setting up PATH and directories..."
mkdir -p "$HOME/.local/bin" "$HOME/.hermes"
if ! grep -q 'PATH=$HOME/.local/bin:$PATH' "$HOME/.bashrc" 2>/dev/null; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
fi

echo "==> Setting up official Hermes launcher wrapper..."
cat << 'LAUNCHER' > "$HOME/.local/bin/hermes"
#!/usr/bin/env bash
unset PYTHONPATH
unset PYTHONHOME
export PATH="$HOME/.local/bin:$PATH"
exec python3.13 -m hermes_cli.main "$@"
LAUNCHER
chmod +x "$HOME/.local/bin/hermes"

echo "==> Setting up patched llama-server wrapper..."
cat << 'LLAMA' > "$HOME/.local/bin/llama-server"
#!/usr/bin/env bash
USER_SITE="$(python3.13 -m site --user-site)"
CUDA_LIB_DIR="${USER_SITE}/nvidia/cu13/lib"
CUBLAS_LIB_DIR="${USER_SITE}/nvidia/cublas/lib"
NVRTC_LIB_DIR="${USER_SITE}/nvidia/cuda_nvrtc/lib"
NCCL_LIB_DIR="${USER_SITE}/nvidia/nccl/lib"
export LD_LIBRARY_PATH="${CUDA_LIB_DIR}:${CUBLAS_LIB_DIR}:${NVRTC_LIB_DIR}:${NCCL_LIB_DIR}:${LD_LIBRARY_PATH}"
exec "$HOME/.local/bin/llama-server.bin" "$@"
LLAMA
chmod +x "$HOME/.local/bin/llama-server"

echo "==> Setup complete! You can now run 'hermes version' or 'llama-server --version'."
