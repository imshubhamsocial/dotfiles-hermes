# Hermes Agent OS — Master Makefile
# Unified developer workflow for setup, testing, plugin sync, and hardware runtime.

.DEFAULT_GOAL := help
SHELL := /usr/bin/env bash

# Directories
WORKSPACE_ROOT := $(shell pwd)
CHEZMOI_DIR    := $(HOME)/.local/share/chezmoi
HERMES_DIR     := $(HOME)/.hermes
BIN_DIR        := $(HOME)/.local/bin
HF_HUB_DIR     := $(HOME)/.cache/huggingface/hub

export PYTHONPATH := $(WORKSPACE_ROOT):$(HERMES_DIR)/hermes-agent:$(PYTHONPATH)

.PHONY: help install sys-deps py-deps node-deps playwright \
        apply-chezmoi models-download server-setup vision-setup \
        searxng test exam doctor clean run-eval \
        chezmoi-sync checkpoint-status checkpoint-prune security guardrails-test \
        codebase-nav-bench memory-graph skills-status \
        plan critique cron-status

help: ## Display this help message
	@echo "Hermes Agent OS — Developer Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

install: sys-deps py-deps node-deps playwright apply-chezmoi server-setup vision-setup ## Complete first-time environment installation
	@echo "✓ Hermes Agent OS fully provisioned."

sys-deps: ## Install system compilers, sandbox, and container utilities via DNF
	@echo "==> Installing base system packages..."
	@sudo dnf install -y gcc gcc-c++ make cmake clang ripgrep fd-find fzf tree htop nvtop \
		bubblewrap e2fsprogs nodejs22 clang-tools-extra gdb valgrind \
		python3.13 python3.13-devel openssl-devel libffi-devel git git-lfs gh chezmoi jq curl wget ksshaskpass

py-deps: ## Install Python dependencies & upstream hermes engine
	@echo "==> Installing Python dependencies..."
	@python3.13 -m ensurepip --upgrade
	@python3.13 -m pip install --break-system-packages setuptools wheel
	@python3.13 -m pip install --break-system-packages \
		pytest playwright \
		pydantic pyyaml rich typer httpx openai fastapi uvicorn starlette \
		python-dotenv prompt_toolkit click requests aiohttp websockets \
		uvloop watchfiles cffi cryptography croniter psutil pillow pathspec ruamel.yaml uv \
		fastembed fastmcp mcp mcp-agent-gate \
		sqlmodel diskcache duckdb instructor flatbuffers \
		tree-sitter==0.26.0 tree-sitter-language-pack==1.15.8 \
		numpy sympy ruff polars pypdf trafilatura tiktoken gguf ddgs crawl4ai \
		openlit opentelemetry-sdk nemoguardrails google-adk \
		nvidia-cuda-runtime nvidia-cublas nvidia-cuda-nvrtc nvidia-nccl-cu13 nvidia-ml-py
	@if [ ! -d "$(HERMES_DIR)/hermes-agent" ]; then \
		echo "==> Cloning upstream NousResearch/hermes-agent..."; \
		git clone --depth 1 https://github.com/NousResearch/hermes-agent.git "$(HERMES_DIR)/hermes-agent"; \
	fi
	@python3.13 -m pip install -e "$(HERMES_DIR)/hermes-agent" --break-system-packages

node-deps: ## Install Node.js LSP servers and formatters
	@echo "==> Installing Node.js CLI tools..."
	@mkdir -p "$(BIN_DIR)" "$(HOME)/.local/lib"
	@npm install -g --prefix "$(HOME)/.local" pyright typescript typescript-language-server prettier @ast-grep/cli pnpm \
		bash-language-server dockerfile-language-server-nodejs vscode-langservers-extracted \
		yaml-language-server eslint @biomejs/biome

playwright: ## Install Playwright Chromium browser & runtime libs
	@echo "==> Installing Playwright Chromium & dependencies..."
	@sudo dnf install -y alsa-lib libX11 libXcomposite libXdamage libXext libXfixes libXrandr libgbm libxkbcommon pango cairo nss nss-util nspr atk at-spi2-atk dbus-glib libdrm mesa-libgbm cups-libs
	@python3.13 -m playwright install chromium

apply-chezmoi: ## Apply dotfiles and sync to ~/.hermes
	@echo "==> Applying chezmoi dotfiles..."
	@chezmoi apply --force

models-download: ## Download Google Gemma-4 QAT Q4_0 & MTP speculative draft models
	@echo "==> Verifying models in standard cache..."
	@python3.13 -c "import os; from huggingface_hub import hf_hub_download; qat_dir = os.path.expanduser('~/.cache/huggingface/hub/models--google--gemma-4-E4B-it-qat-q4_0-gguf/snapshots/main'); mtp_dir = os.path.expanduser('~/.cache/huggingface/hub/models--bartowski--gemma-4-E4B-it-GGUF/snapshots/main'); os.makedirs(qat_dir, exist_ok=True); os.makedirs(mtp_dir, exist_ok=True); [hf_hub_download(repo_id='google/gemma-4-E4B-it-qat-q4_0-gguf', filename='gemma-4-E4B_q4_0-it.gguf', local_dir=qat_dir) if not os.path.exists(os.path.join(qat_dir, 'gemma-4-E4B_q4_0-it.gguf')) else None]; [hf_hub_download(repo_id='bartowski/gemma-4-E4B-it-GGUF', filename='mtp-gemma-4-E4B-it-Q4_0.gguf', local_dir=mtp_dir) if not os.path.exists(os.path.join(mtp_dir, 'mtp-gemma-4-E4B-it-Q4_0.gguf')) else None]"

define LLAMA_SERVER_SCRIPT
#!/usr/bin/env bash
set -euo pipefail
SITE_PACKAGES="$$(python3 -m site --user-site 2>/dev/null || python3.14 -m site --user-site 2>/dev/null || python3.13 -m site --user-site 2>/dev/null || echo "$${HOME}/.local/lib/python3.14/site-packages")"
LLAMA_LIB_DIR="$${HOME}/.local/lib:$${WORKSPACE_ROOT:-$$(pwd)}/.local/lib"
SERVER_BIN="$${HOME}/.local/bin/llama-server.bin"
export LD_LIBRARY_PATH="$${LLAMA_LIB_DIR}:$${SITE_PACKAGES}/nvidia/cu13/lib:$${SITE_PACKAGES}/nvidia/cublas/lib:$${SITE_PACKAGES}/nvidia/cuda_nvrtc/lib:$${SITE_PACKAGES}/nvidia/nccl/lib:$${SITE_PACKAGES}/nvidia/cuda_runtime/lib:$${HOME}/.local/share/cuda-libs:$${LD_LIBRARY_PATH:-}"
HF_HUB_DIR="$${HF_HUB_DIR:-$${WORKSPACE_ROOT:-$$(pwd)}/.cache/huggingface/hub}"
if [[ ! -d "$$HF_HUB_DIR" && -d "$${HOME}/.cache/huggingface/hub" ]]; then
    HF_HUB_DIR="$${HOME}/.cache/huggingface/hub"
fi
MODEL_MAIN="$${HF_HUB_DIR}/models--google--gemma-4-E4B-it-qat-q4_0-gguf/snapshots/main/gemma-4-E4B_q4_0-it.gguf"
MODEL_DRAFT="$${HF_HUB_DIR}/models--bartowski--gemma-4-E4B-it-GGUF/snapshots/main/mtp-gemma-4-E4B-it-Q4_0.gguf"
DRAFT_FLAGS=()
if [[ -f "$$MODEL_DRAFT" ]]; then
    DRAFT_FLAGS=(--model-draft "$$MODEL_DRAFT" --spec-type draft-mtp --spec-draft-ngl 99 --spec-draft-n-max 3 --spec-draft-p-min 0.00)
fi
exec "$$SERVER_BIN" --model "$$MODEL_MAIN" "$${DRAFT_FLAGS[@]}" --alias "google/gemma-4-E4B-it,dory" -ngl 99 --flash-attn on --backend-sampling --jinja --reasoning on --reasoning-format auto -c 65536 -b 2048 -ub 512 --cache-type-k q4_0 --cache-type-v q4_0 -np 1 --slot-save-path "$${HOME}/.hermes/cache/slots" --threads 6 --threads-batch 6 --host 127.0.0.1 --port 8138 --metrics --temp 0.2 --top-p 0.95 --top-k 64 --repeat-penalty 1.0 "$$@"
endef
export LLAMA_SERVER_SCRIPT

server-setup: ## Configure llama-server daemon launcher with hardware VRAM ceiling
	@echo "==> Provisioning llama-server launcher..."
	@mkdir -p "$(BIN_DIR)" "$(HERMES_DIR)/cache/slots"
	@printf '%s\n' "$$LLAMA_SERVER_SCRIPT" > "$(BIN_DIR)/llama-server"
	@chmod +x "$(BIN_DIR)/llama-server"

define VISION_SERVER_SCRIPT
#!/usr/bin/env bash
set -euo pipefail
SITE_PACKAGES="$$(python3 -m site --user-site 2>/dev/null || python3.14 -m site --user-site 2>/dev/null || python3.13 -m site --user-site 2>/dev/null || echo "$${HOME}/.local/lib/python3.14/site-packages")"
LLAMA_LIB_DIR="$${HOME}/.local/lib:$${WORKSPACE_ROOT:-$$(pwd)}/.local/lib"
SERVER_BIN="$${HOME}/.local/bin/llama-server.bin"
export CUDA_VISIBLE_DEVICES=""
export LD_LIBRARY_PATH="$${LLAMA_LIB_DIR}:$${SITE_PACKAGES}/nvidia/cu13/lib:$${SITE_PACKAGES}/nvidia/cublas/lib:$${SITE_PACKAGES}/nvidia/cuda_nvrtc/lib:$${SITE_PACKAGES}/nvidia/nccl/lib:$${SITE_PACKAGES}/nvidia/cuda_runtime/lib:$${HOME}/.local/share/cuda-libs:$${LD_LIBRARY_PATH:-}"
VISION_MODEL_DIR="$${VISION_MODEL_DIR:-$${HOME}/.cache/models/vision}"
exec "$$SERVER_BIN" \
    --model "$$VISION_MODEL_DIR/SmolVLM2-256M-Video-Instruct-Q4_K_M.gguf" \
    --mmproj "$$VISION_MODEL_DIR/mmproj-SmolVLM2-256M-Video-Instruct-Q8_0.gguf" \
    -ngl 0 -c 4096 --threads 4 --host 127.0.0.1 --port 8139 "$$@"
endef
export VISION_SERVER_SCRIPT

vision-setup: ## Configure SmolVLM2 vision sidecar launcher on CPU
	@echo "==> Provisioning vision-server launcher..."
	@mkdir -p "$(BIN_DIR)"
	@printf '%s\n' "$$VISION_SERVER_SCRIPT" > "$(BIN_DIR)/hermes-vision"
	@chmod +x "$(BIN_DIR)/hermes-vision"

searxng: ## Ensure local SearXNG container daemon is running on port 8080
	@if command -v podman &>/dev/null; then \
		podman start searxng-hermes 2>/dev/null || podman run -d --name searxng-hermes --restart=always -p 8080:8080 docker.io/searxng/searxng:latest || true; \
	fi

test: doctor ## Run Hermes doctor diagnostics and verification
	@echo "✓ Diagnostics complete."

doctor: ## Run Hermes system health diagnostics
	@hermes doctor

exam: doctor ## Run system health diagnostics
	@echo "✓ All exam checks passed."

security: ## Run OSV.dev supply-chain vulnerability scan across installed components
	@distrobox enter ws-hermes -- hermes security audit

guardrails-test: ## Verify upstream NVIDIA NeMo Guardrails library actions
	@distrobox enter ws-hermes -- python3 -c 'from nemoguardrails.library.sensitive_data_detection.actions import detect_sensitive_data; from nemoguardrails.library.jailbreak_detection.actions import jailbreak_detection_heuristics; print("✓ NVIDIA NeMo Guardrails upstream modules active.")'

run-eval: ## Launch canonical testbed evaluation (ast_grep_eval)
	@distrobox enter ws-hermes -- hermes --in tests/ast_grep_eval "Search calculate_fibonacci using ast-grep and compile with gcc"

clean: ## Clean up temporary bytecode and pytest caches
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Clean complete."

chezmoi-sync: ## Synchronize ~/.hermes configuration into Chezmoi repository
	@distrobox enter ws-hermes -- chezmoi re-add .hermes
	@echo "✓ Chezmoi parity synchronized."

checkpoint-status: ## Show filesystem checkpoint store status and size
	@distrobox enter ws-hermes -- hermes checkpoints status

checkpoint-prune: ## Delete orphan/stale checkpoints and GC the store
	@distrobox enter ws-hermes -- hermes checkpoints prune

codebase-nav-bench: ## Run upstream codebase navigability benchmark
	@mkdir -p .hermes/evals/nav_bench
	@distrobox enter ws-hermes -- .hermes/hermes-agent/venv/bin/python3 .hermes/hermes-agent/evals/codebase_navigability/bench.py .hermes/hermes-agent baseline --out .hermes/evals/nav_bench
	@echo "✓ Navigability benchmark complete."

memory-graph: ## Visualize entity-relationship memory graph
	@distrobox enter ws-hermes -- hermes memory-graph --json

skills-status: ## List installed skills and trust status
	@distrobox enter ws-hermes -- hermes skills list

plan: ## Decompose a task into specialist subtasks via Kanban
	@distrobox enter ws-hermes -- hermes kanban decompose

critique: ## Run deterministic diff-aware critique via reviewdog and linters
	@distrobox enter ws-hermes -- bash -c 'PATH=$$HOME/.local/bin:$$PATH reviewdog -diff="git diff" -reporter=local'

cron-status: ## Show all scheduled jobs and their health status
	@distrobox enter ws-hermes -- hermes cron list

mcp-status: ## List configured MCP servers and tool counts
	@distrobox enter ws-hermes -- hermes mcp list

