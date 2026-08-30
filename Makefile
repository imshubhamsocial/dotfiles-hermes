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

.PHONY: help install sys-deps py-deps node-deps playwright \
        plugins-sync apply-chezmoi models-download server-setup \
        searxng test test-contracts test-domain exam doctor clean

help: ## Display this help message
	@echo "Hermes Agent OS — Developer Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

install: sys-deps py-deps node-deps playwright apply-chezmoi plugins-sync server-setup ## Complete first-time environment installation
	@echo "✓ Hermes Agent OS fully provisioned."

sys-deps: ## Install system compilers, sandbox, and container utilities via DNF
	@echo "==> Installing base system packages..."
	@sudo dnf install -y gcc gcc-c++ make cmake clang ripgrep fd-find fzf tree htop nvtop \
		bubblewrap e2fsprogs nodejs22 clang-tools-extra gdb valgrind \
		python3.13 python3.13-devel openssl-devel libffi-devel git git-lfs chezmoi jq curl wget ksshaskpass

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
		numpy sympy ruff polars pypdf trafilatura tiktoken gguf ddgs \
		nvidia-cuda-runtime nvidia-cublas nvidia-cuda-nvrtc nvidia-nccl-cu13 nvidia-ml-py
	@if [ ! -d "$(HERMES_DIR)/hermes-agent" ]; then \
		echo "==> Cloning upstream NousResearch/hermes-agent..."; \
		git clone --depth 1 https://github.com/NousResearch/hermes-agent.git "$(HERMES_DIR)/hermes-agent"; \
	fi
	@python3.13 -m pip install -e "$(HERMES_DIR)/hermes-agent" --break-system-packages
	@python3.13 -m pip install --break-system-packages "$(CHEZMOI_DIR)"

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
	@python3.13 -m pip install --break-system-packages "$(CHEZMOI_DIR)"

plugins-sync: apply-chezmoi ## Synchronize all plugins declared in hermes-pack.yaml
	@echo "==> Syncing plugins from hermes-pack.yaml..."
	@for p in quorum_audit gepa_optimizer observer_gate cog_verifier agent_os symbol_index recirculation_adapter reflective_learner_adapter synergy_bus_adapter; do \
		hermes plugins enable "$$p" 2>/dev/null || true; \
	done
	@hermes plugins list --no-bundled

models-download: ## Download Gemma-4 Q4_K_M & MTP speculative draft models
	@echo "==> Verifying models in standard cache..."
	@python3.13 -c "import os; from huggingface_hub import hf_hub_download; target_dir = os.path.expanduser('~/.cache/huggingface/hub/models--bartowski--gemma-4-E4B-it-GGUF/snapshots/main'); os.makedirs(target_dir, exist_ok=True); [hf_hub_download(repo_id=repo, filename=fn, local_dir=target_dir) for fn, repo in [('gemma-4-E4B-it-Q4_K_M.gguf', 'bartowski/gemma-4-E4B-it-GGUF'), ('mtp-gemma-4-E4B-it-Q4_0.gguf', 'bartowski/gemma-4-E4B-it-GGUF')] if not os.path.exists(os.path.join(target_dir, fn))]"

server-setup: ## Configure llama-server daemon launcher with hardware VRAM ceiling
	@echo "==> Provisioning llama-server launcher..."
	@mkdir -p "$(BIN_DIR)" "$(HERMES_DIR)/cache/slots"
	@cat << 'LLAMA' > "$(BIN_DIR)/llama-server"
	#!/usr/bin/env bash
	set -euo pipefail
	SITE_PACKAGES="$$(python3.13 -m site --user-site 2>/dev/null || echo "$${HOME}/.local/lib/python3.13/site-packages")"
	LLAMA_LIB_DIR="$${HOME}/.local/lib"
	SERVER_BIN="$${HOME}/.local/bin/llama-server.bin"
	export LD_LIBRARY_PATH="$${LLAMA_LIB_DIR}:$${SITE_PACKAGES}/nvidia/cu13/lib:$${SITE_PACKAGES}/nvidia/cublas/lib:$${SITE_PACKAGES}/nvidia/cuda_nvrtc/lib:$${SITE_PACKAGES}/nvidia/nccl/lib:$${SITE_PACKAGES}/nvidia/cuda_runtime/lib:$${HOME}/.local/share/cuda-libs:$${LD_LIBRARY_PATH:-}"
	HF_HUB_DIR="$${HF_HUB_DIR:-$${HOME}/.cache/huggingface/hub}"
	MODEL_MAIN="$${HF_HUB_DIR}/models--bartowski--gemma-4-E4B-it-GGUF/snapshots/main/gemma-4-E4B-it-Q4_K_M.gguf"
	MODEL_DRAFT="$${HF_HUB_DIR}/models--bartowski--gemma-4-E4B-it-GGUF/snapshots/main/mtp-gemma-4-E4B-it-Q4_0.gguf"
	DRAFT_FLAGS=()
	if [[ -f "$$MODEL_DRAFT" ]]; then
	    DRAFT_FLAGS=(--model-draft "$$MODEL_DRAFT" --spec-draft-ngl 99 --spec-draft-n-max 3)
	fi
	exec "$$SERVER_BIN" --model "$$MODEL_MAIN" "$${DRAFT_FLAGS[@]}" -ngl 99 --flash-attn on --jinja -c 131072 --cache-type-k q4_0 --cache-type-v q4_0 -np 2 --slot-save-path "$${HOME}/.hermes/cache/slots" --threads 6 --threads-batch 6 --host 127.0.0.1 --port 8138 --metrics --temp 1.0 --top-p 0.95 --top-k 64 "$$@"
	LLAMA
	@chmod +x "$(BIN_DIR)/llama-server"

searxng: ## Ensure local SearXNG container daemon is running on port 8080
	@if command -v podman &>/dev/null; then \
		podman start searxng-hermes 2>/dev/null || podman run -d --name searxng-hermes --restart=always -p 8080:8080 docker.io/searxng/searxng:latest || true; \
	fi

test: test-contracts test-domain ## Run full 620-test contract and domain test suites
	@echo "✓ All 620 contract and domain tests passed."

test-contracts: ## Run 602 contract test spikes
	@python3.13 -m pytest tests/harness_contracts/ -q

test-domain: ## Run domain persistence, FastMCP, and Quorum/GEPA tests
	@python3.13 -m pytest tests/test_fastmcp_transport.py tests/test_domain4_persistence.py tests/test_domain5_security_delegation.py tests/test_quorum_and_gepa.py -q

exam: ## Run final live integration exam and capability verification
	@python3.13 tests/runners/run_final_integration_exam.py
	@python3.13 $(HERMES_DIR)/bin/verify_harness_integrity.py


doctor: ## Run Hermes system health and plugin contract diagnostics
	@hermes doctor
	@for p in quorum_audit gepa_optimizer observer_gate cog_verifier agent_os symbol_index recirculation_adapter reflective_learner_adapter synergy_bus_adapter; do \
		hermes plugins doctor "$$p"; \
	done

clean: ## Clean up temporary bytecode and pytest caches
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Clean complete."
