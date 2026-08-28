# Hermes Agent OS & Living Harness

> **A High-Performance, Turnkey Autonomous Agent Operating System on Local Silicon**  
> Calibrated for 4B/8B Small Language Models (SLMs) with Zero-Bloat Prefix Caching, SQLite WAL TaskDAGs, and Hardware-Hardened Sandboxing.

---

## Table of Contents

- [1. Executive Overview](#1-executive-overview)
- [2. System Architecture & Core Principles](#2-system-architecture--core-principles)
- [3. Local LLM Runtime: llama.cpp & Gemma-4-4B](#3-local-llm-runtime-llamacpp--gemma-4-4b)
  - [3.1. Hardware Allocation & Budget](#31-hardware-allocation--budget)
  - [3.2. Patched llama-server Wrapper & Kernel Flags](#32-patched-llama-server-wrapper--kernel-flags)
  - [3.3. Prefix-Cache & KV-Cache Configuration](#33-prefix-cache--kv-cache-configuration)
- [4. Hermes Harness & Subsystems](#4-hermes-harness--subsystems)
  - [4.1. 7-Layer Agent OS Architecture](#41-7-layer-agent-os-architecture)
  - [4.2. Cognitive Guardrails & Observer Gates](#42-cognitive-guardrails--observer-gates)
  - [4.3. Hybrid Retrieval & LoRA Hot-Swapping](#43-hybrid-retrieval--lora-hot-swapping)
- [5. Repository Structure](#5-repository-structure)
- [6. Setup & Turnkey Portability](#6-setup--turnkey-portability)
- [7. Operational Commands & CLI Guide](#7-operational-commands--cli-guide)
- [8. Documentation & Roadmaps](#8-documentation--roadmaps)

---

## 1. Executive Overview

**Hermes Agent OS** is a fully autonomous pair-programming and code-generation harness designed to elevate lightweight open-weights models (such as `Gemma-4-4B` and `Gemma-3-4B`) to production parity with frontier enterprise assistants (e.g., Google Antigravity CLI and OpenAI Codex).

The harness achieves deterministic performance through:
1. **Deterministic System-2 Decomposition**: Enforcing structured planning contracts (`.hermes/plan.json`) and topological SQLite WAL task DAGs before code generation.
2. **Strict Hardware-Calibrated Budgets**: Bounding token expenditure, eliminating context drift via $>90\%$ prefix-cache hits, and maintaining a hard $\le 4,812\text{ MiB}$ VRAM ceiling on an NVIDIA RTX 3050 Laptop GPU (6 GB).
3. **Clean-Room Verification & Pre-Commit Gates**: Automated AST linting, headless Playwright WebGL kinematic testing, and tabu branch pruners that prevent looping regressions.

---

## 2. System Architecture & Core Principles

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   HERMES 7-LAYER AGENT OS ARCHITECTURE                           │
├─────────┬───────────────────────────────┬────────────────────────────────────────────────────────┤
│ Layer   │ Subsystem Name                │ Primary Responsibility                                 │
├─────────┼───────────────────────────────┼────────────────────────────────────────────────────────┤
│ Layer 1 │ Core Primitives               │ SQLite WAL TaskDAG, Transactional Memory, File Safety  │
│ Layer 2 │ Sandboxing & Safety           │ Bubblewrap (bwrap) Jail, PGID Process Isolation Guard  │
│ Layer 3 │ Token Economy                 │ Prefix-Cache Alignment, Differential History Compactor │
│ Layer 4 │ Trajectory & Lineage          │ SHA-256 Event Chain, Deterministic Replay Runner       │
│ Layer 5 │ Neural & Search Engines       │ CPU ONNX BGE Embeddings, Hybrid RRF Vector Search      │
│ Layer 6 │ Agent OS Kernel & Daemons     │ 7-Layer Event Coordinator, Prime Execution Kernel      │
│ Layer 7 │ Metacognitive & Observer      │ Multi-Gate Observer, AST Verification, Tabu Pruner     │
└─────────┴───────────────────────────────┴────────────────────────────────────────────────────────┘
```

### The 8 Golden Laws of the Living Harness:
1. **Zero-Token Waste**: Never feed raw file dumps into LLM context; use PageRank spines and targeted AST slices.
2. **Deterministic Planning First**: Always draft and persist formal specifications in `.hermes/plan.json` prior to tool execution.
3. **Prefix-Cache Determinism**: Fixed byte-identical system prompts must precede dynamic user turns to ensure $>90\%$ prompt cache hits.
4. **VRAM Guard Invariant**: Total GPU allocation across base weights, KV cache, and active LoRA adapters must never exceed $4,812\text{ MiB}$.
5. **No Blind Commits**: Every code mutation must pass the 6-point Observer Gate (AST syntax, brace balance, scope mutation, size checks).
6. **Aggressive Hypothesis Pruning**: Auto-swap branches on 2 consecutive test failures to prevent repetitive fixations.
7. **Clean-Room Subagent Isolation**: Subagents execute in isolated scratchpads with strict capabilities masks and read-only defaults.
8. **100% Turnkey Portability**: Zero hardcoded paths; everything paths relative to `$HOME` and is synchronized via Chezmoi.

---

## 3. Local LLM Runtime: llama.cpp & Gemma-4-4B

The inference engine runs locally via a customized, CUDA-accelerated `llama-server` runtime with dynamic runtime library injection.

### 3.1. Hardware Allocation & Budget

| Component | Target Allocation | Measured Value | Operational Guardrail |
| :--- | :---: | :---: | :--- |
| **GPU Model** | NVIDIA RTX 3050 (Laptop) | 6,144 MiB VRAM | Hardware Ceiling |
| **Base Model Weights** | `gemma-4-E4B-it-Q4_K_M.gguf` | $\approx 2,450\text{ MiB}$ | 100% GPU Offloaded (`-ngl 99`) |
| **Speculative Draft Model** | `mtp-gemma-4-E4B-it-Q4_0.gguf` | $\approx 57\text{ MiB}$ | 100% GPU Offloaded (`--spec-draft-ngl 99`) |
| **KV Cache Allocation** | 65,536 Tokens in `q4_0` | $\approx 1,248\text{ MiB}$ | `--cache-type-k q4_0 --cache-type-v q4_0` |
| **Total Server Footprint** | Static In-Memory | **$\approx 3,745\text{ MiB}$** | **Budget: $\le 4,812\text{ MiB}$ (PASS)** |
| **Prefill Throughput** | Flash-Attention Accelerated | **$675.60\text{ tokens/sec}$** | Instant multi-turn prompt ingestion |
| **Decoding Speed** | MTP Speculative Accelerated | **$35\text{–}48\text{ tokens/sec}$** | 3-token speculative multi-drafting |

### 3.2. Patched llama-server Wrapper & Kernel Flags

The launcher wrapper is located at `~/.local/bin/llama-server`. It dynamically binds the user-site NVIDIA CUDA 13/cuBLAS runtime libraries and initiates inference with strict hardware-calibrated flags:

```bash
#!/usr/bin/env bash
USER_SITE="$(python3.13 -m site --user-site 2>/dev/null || echo "$HOME/.local/lib/python3.13/site-packages")"
LLAMA_LIB_DIR="${HOME}/bin/llama"
export LD_LIBRARY_PATH="${LLAMA_LIB_DIR}:${USER_SITE}/nvidia/cu13/lib:${USER_SITE}/nvidia/cublas/lib:${USER_SITE}/nvidia/cuda_nvrtc/lib:${USER_SITE}/nvidia/nccl/lib:${LD_LIBRARY_PATH}"

MODEL_MAIN="${HOME}/assets/gguf/gemma-4-E4B-it-Q4_K_M.gguf"
MODEL_DRAFT="${HOME}/assets/MTP/mtp-gemma-4-E4B-it-Q4_0.gguf"
SERVER_BIN="${HOME}/bin/llama/llama-server.bin"

exec "$SERVER_BIN" \
    --model "$MODEL_MAIN" \
    --model-draft "$MODEL_DRAFT" \
    --spec-draft-n-max 3 \
    --spec-draft-n-min 1 \
    -ngl 99 \
    --spec-draft-ngl 99 \
    --flash-attn on \
    --jinja \
    -c 65536 \
    --cache-type-k q4_0 \
    --cache-type-v q4_0 \
    --threads 6 \
    --threads-batch 6 \
    --cpu-range 0-11 \
    --cpu-strict 1 \
    --host 127.0.0.1 \
    --port 8138 \
    --metrics \
    "$@"
```

### 3.3. Key Acceleration Flags Explained

* **Multi-Token Prediction (`--model-draft ... --spec-draft-n-max 3`)**: Speculatively drafts up to 3 tokens per step using the lightweight $57\text{ MB}$ MTP head, verifying them in parallel on the GPU for $2.5\times\text{–}3.3\times$ faster token decoding.
* **Flash Attention (`--flash-attn on`)**: Computes fused self-attention directly inside GPU SRAM, lifting prompt prefill throughput to **$675.6\text{ tok/s}$** ($27\times$ speedup over unfused attention).
* **Jinja Tool-Calling DSL (`--jinja`)**: Renders native Gemma-4 tool-calling schemas and parallel function call blocks with zero JSON deserialization errors.
* **Quantized KV Cache (`--cache-type-k q4_0 --cache-type-v q4_0`)**: Slashes KV-cache memory usage by $75\%$, enabling full **64,536 context** within $\approx 1.25\text{ GB}$ VRAM.
* **Thread & CPU Core Pinning (`--cpu-range 0-11 --cpu-strict 1`)**: Binds compute threads strictly to physical CPU cores, preventing Linux scheduler context switches.

---

## 4. Hermes Harness & Subsystems

### 4.1. 7-Layer Agent OS Architecture

* **TaskDAG Engine (`task_graph.py`)**: Persistent SQLite WAL DAG that schedules milestones topographically, tracks parent-child dependencies, and handles rollbacks.
* **Symbol Graph (`symbol_graph.py`)**: In-memory and RAMDisk AST symbol indexer extracting functions, classes, and cross-file references.
* **Bubblewrap Jail (`sandbox.py`)**: Hardened OS isolation preventing unauthorized file overwrites, masking `/etc/shadow`, and restricting network egress.

### 4.2. Cognitive Guardrails & Observer Gates

* **Pre-Commit Observer Gate (`observer_gate.py`)**: Runs 6 verification gates (HTML/JS AST syntax, brace balance, duplicate declarations, clean-room contamination guard, and token bloat blocks).
* **Kinematic & Visual Arbiter (`visual_arbiter.py`)**: Uses headless Playwright to capture WebGL canvas frames and assert spatial/rotational velocity ($\Delta \text{pos} > 0$).
* **Hypothesis Tree Branch Swapper (`branch_swapper.py`)**: Tracks attempts and resets workspace to parent git commits with injected negative constraints if a repair fails twice.

### 4.3. Hybrid Retrieval & LoRA Hot-Swapping

* **BGE Neural Template Retriever (`template_retriever.py`)**: Runs `BAAI/bge-small-en-v1.5` on **CPU ONNX** ($0\text{ MB GPU}$) to retrieve verified code skeletons (Three.js WebGL, Python AST, C++20 RAII) and inject them before LLM synthesis.
* **LoRA Adapter Manager (`lora_adapter_manager.py`)**: Dynamic routing for generic languages (`python_core`, `javascript_ts`, `modern_cpp`) and specialized domains (`threejs_kinematics`, `ast_grammar_guard`) with a strict $<150\text{ MB}$ VRAM guard.

---

## 5. Repository Structure & Canonical Upstream Layout

```
~ (Host $HOME)
├── ~/.local/
│   ├── bin/                            # Standalone CLI executables (hermes, llama-server, llama-server.bin)
│   └── lib/                            # Upstream shared libraries (libggml*.so, libllama*.so, libmtmd*.so)
│
├── ~/.cache/
│   ├── huggingface/hub/                # Standard model weight cache (Gemma-4 + MTP drafter)
│   └── cpython/                        # Centralized bytecode cache (zero repository pollution)
│
├── ~/.hermes/                          # Canonical Upstream Hermes Runtime Substrate
│   ├── config.yaml                     # Hardware configurations, context engine & plugin toggles
│   ├── rules/                          # Two-tier immutable kernel & project behavioral standards
│   ├── skills/                         # OpenSkills progressive context stubs (L0/L1/L2)
│   ├── scripts/                        # Daemon scripts (start_server_daemon.sh)
│   ├── bin/                            # Verification & gate scripts (observer_gate.py, verify_harness_integrity.py)
│   ├── plugins/                        # Native standalone plugins (agent_os, cog_verifier, symbol_index)
│   ├── src/hermes_core/                # Cognitive OS subsystems & Python engine sources
│   └── hermes-agent/                   # Upstream Hermes Agent engine
│
├── tests/                              # Comprehensive test suites & contract spikes
│   ├── harness_contracts/              # 602 passed contract tests verifying all capabilities
│   └── oracle_references/              # Gold-standard baseline benchmarks
│
├── docs/                               # Professional documentation hierarchy
│   ├── roadmaps/                       # Architectural roadmaps (Roadmaps 1-5 completed)
│   ├── operations/                     # Operational guides & environment context
│   └── prompts/                        # System prompts & Claude evaluation prompts
│
├── pyproject.toml                      # Package build configuration
├── packages.json                       # System package manifests for DNF, Python & Node CLI
└── setup.sh                            # Turnkey installer (DNF, pip, Playwright, models, SearXNG)
```

---

## 6. Setup & Turnkey Portability

The harness is engineered to be 100% portable across machines (Fedora Workstation/KDE, Fedora Kinoite/Silverblue, or native Linux servers) without hardcoded paths.

### Fresh Machine Bootstrap in 2 Commands:

```bash
# Preliminary bootstrap packages (on a fresh PC)
sudo dnf install -y git chezmoi git-lfs ksshaskpass

# 1. Initialize and apply dotfiles & harness configurations
# Recommended (uses SSH key with zero prompt timeout):
chezmoi init --apply git@github.com:imshubhamsocial/dotfiles-hermes.git

# Or via HTTPS (requires GitHub credentials / PAT):
# chezmoi init --apply https://github.com/imshubhamsocial/dotfiles-hermes.git

# 2. Run automated turnkey installer (DNF packages, Python toolchains, Playwright, Node CLIs, model download, SearXNG autostart)
bash setup.sh
```

---

## 7. Operational Commands & CLI Guide

```bash
# Start background llama-server daemon locked to Intel P-Cores (0-11)
bash .hermes/scripts/start_server_daemon.sh

# Launch Hermes CLI with autonomous prompt execution
hermes -z "Decompose and build a 3D Solar System simulation in index.html" --yolo

# Run full harness capability and contract test audit (30/30 capabilities)
python3.13 .hermes/bin/verify_harness_integrity.py

# Run all 602 contract unit tests
python3.13 -m pytest tests/harness_contracts/ -v

# Run pre-commit observer gate manually on a file
python3.13 .hermes/bin/observer_gate.py src/main.js
```

---

## 8. Documentation & Roadmaps

Detailed specifications are organized in the [`docs/`](./docs/README.md) directory:

* 🗺️ **[Roadmap 1: Master Autonomous Test Plan](./docs/roadmaps/completed/roadmap1_master_test_plan.md)**: Baseline capabilities U1–U20.
* 🗺️ **[Roadmap 2: Agent OS Substrate](./docs/roadmaps/completed/roadmap2_agent_os_substrate.md)**: 7-Layer substrate U21–U35.
* 🗺️ **[Roadmap 3: Production Graduation](./docs/roadmaps/completed/roadmap3_production_graduation.md)**: Production parity U36–U44.
* 🗺️ **[Roadmap 4: Frontier Cognitive OS](./docs/roadmaps/completed/roadmap4_frontier_cognitive_os.md)**: Memory graphs, NVIDIA Skill Lift, DeepMind Recirculation U45–U60.
* 🗺️ **[Roadmap 5: Multi-Agent Web Intelligence](./docs/roadmaps/completed/roadmap5_frontier_multiagent_web_intelligence.md)**: SearXNG grounding, Multi-Agent Swarm U61–U80.
