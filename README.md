---
title: "Hermes Agent OS & Living Harness"
version: "3.0.0-AGY-FRONTIER"
runtime: "ws-hermes"
model: "gemma-4-E4B-it-Q4_K_M.gguf"
hardware_requirements:
  gpu_vram_limit_mib: 4800
  context_window_tokens: 65536
  kv_cache: "q4_0"
capabilities:
  - "google-antigravity-2.0-artifacts"
  - "gemini-thought-signature-preservation"
  - "hierarchical-rule-progressive-disclosure"
  - "magentic-one-dual-ledgers-stall-breaker"
  - "google-jules-worktree-isolation"
  - "agent2agent-a2a-protocol-cards"
  - "bpe-memory-workspace"
  - "meta-harness-self-evolution"
  - "trajectory-sqlite-observability"
  - "smolagents-code-as-action"
  - "aider-search-replace-diffs"
  - "nemo-guardrails-colang-2.0"
  - "shannon-entropy-execution-rails"
  - "deterministic-ast-code-prm"
  - "frognano-learnability-frontier"
  - "hybrid-context-budget-router"
  - "ecc-agentshield-security"
  - "autonomous-dag-planning"
  - "generative-ui-html-aux-pane"
  - "litho-c4-architecture-docs"
  - "quorum-maker-verifier-gate"
  - "zero-wrapper-native-subcommands"

tags:
  - "agent-os"
  - "antigravity"
  - "jules"
  - "local-slm"
  - "gemma-4"
  - "self-evolving-superintelligence"
  - "harness-engineering"
---

# Hermes Agent OS & Living Harness (Era 10)

> **Google AGY-Ready Self-Learning Superintelligence Harness on Consumer Silicon**  
> Calibrated for 4B/8B Small Language Models (SLMs) with Zero-Bloat Prefix Caching, Antigravity 2.0 Bridge, Magentic-One Dual Ledgers, BPE Workspaces, Trajectory DB, and Hardware-Hardened Sandboxing (**10/10 In-Process Verification Contracts Passing**).

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
hermes/ (workspace root)
├── AGENTS.md                  # Definitive operating standard for AI coding agents
├── README.md                  # Project overview, quickstart, and feature matrix
├── Makefile                   # Unified developer targets (sys-deps, py-deps, node-deps)
├── pyproject.toml             # Single canonical Python manifest (PEP 621 dependencies, ruff, pytest)
├── package.json               # Node.js devDependencies (ast-grep, Biome, prettier, pyright)
├── requirements.txt           # Minimal pointer (-e .[dev,benchmark,vision]) linking to pyproject.toml
│
├── docs/                      # Consolidated, single-source-of-truth documentation suite
│   ├── README.md              # Documentation index and quickstart guide
│   ├── architecture.md        # System architecture, C4 diagrams, 28 plugins, flow, filesystem
│   ├── research.md            # Master chronological research register (62 items & 8 ADRs)
│   ├── verification.md        # 10 in-process verification harnesses, benchmarks, cron daemons
│   └── integrations.md        # FastMCP Open-Notebook, Port 8139 Vision, CUA, Antigravity Bridge
│
├── .hermes/                   # Complete encapsulated runtime substrate (mirrored to ~/.hermes)
│   ├── bin/                   # 10 executable verification harnesses (Horizons 1–5, Phases 0–4)
│   ├── cron/                  # Scheduled daemons (daily_health_check, weekly_evolution, weekly_sync)
│   ├── plugins/               # 28 capability plugins
│   ├── rules/                 # Inferred behavioral invariants & system prompt rules
│   ├── scripts/               # Operational utility scripts
│   ├── SOUL.md                # 176-line cognitive system identity prompt
│   └── config.yaml            # Master configuration for models, plugins, and gateways
│
└── ~/.local/share/chezmoi/    # Chezmoi dotfiles git repository tracking private_dot_hermes/
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
# 1. Start background llama-server daemon locked to Intel P-Cores (0-11)
bash .hermes/scripts/start_server_daemon.sh

# 2. Run master final integration exam against live champion model
make exam

# 3. Run full system health & plugin diagnostic suite (v37 schema)
make doctor

# 4. Zero-Test-Folder Architecture: Run 100% self-contained native capability audit (20 probes)
python3.13 .hermes/bin/verify_harness_integrity.py --standalone

# 5. Launch Hermes CLI with autonomous prompt execution & YOLO mode
hermes -z "Audit codebase AST graph and propose architecture refactor" --yolo

# 6. Generate codebase knowledge graph & Markdown wiki via decoupled Graphify AST engine
python3.13 .hermes/scripts/build_codebase_graph.py

# 7. Benchmark CPU ONNX embedding models (EmbeddingGemma 308M vs BGE-Small 33M)
python3.13 .hermes/scripts/benchmark_embeddings.py

# 8. Train & export domain QLoRA adapter with non-regression verification
python3.13 .hermes/scripts/train_qlora_adapter.py --domain python_core --rank 16

# 9. Run pre-commit observer gate manually on a file
python3.13 .hermes/bin/observer_gate.py src/main.js
```

---

## 8. Advanced Cognitive Subsystems (Tracks 1, 3, 4 & Google Env-Harness Standard)

### 8.1. Decoupled Codebase Knowledge Graph (Track 1)
- **Engine**: Headless `graphifyy` parser isolated strictly in `~/.local/share/graphify-env` (Law #8 Zero Core Contamination).
- **Substrate**: Generates dependency graphs, community clusters, and god node reports in `graphify-out/`.
- **Knowledge Bridge**: Automatically indexes Markdown wiki cards on RAMDisk (`/dev/shm`) accessible via `second_brain.py` in sub-8ms with zero LLM query overhead.

### 8.2. Reasoning & Retrieval Upgrades (Track 3)
- **Gemma-APS in DraftDetective**: Abstractive Proposition Segmentation breaks generated claims into atomic assertions (signatures, default values, return types, exceptions, classes) and verifies them against the ground-truth AST prior to committing.
- **EmbeddingGemma On-Device Evaluation**: Profiling `google/embeddinggemma-300m` on CPU ONNX; leverages Gemma's 256k vocabulary (1.69 tokens/symbol on code vs BGE's 3.77), reducing subword fragmentation with 0 MB GPU VRAM contention.

### 8.3. Self-Correction, Adapters & Vision (Track 4)
- **Cactus Hybrid Uncertainty Detection**: Fuses verbalized hedging entropy, structural blast-radius risk, and failure streaks ($U \in [0.0, 1.0]$). Triggers `STOP_UNCERTAINTY_BREACH` halt in `LoopController` and generates targeted clarification prompts when $U \ge 0.70$.
- **Unsloth On-Device QLoRA Adapter Manager**: Dynamic hot-swapping across 5 domain adapters (`python_core`, `javascript_ts`, `modern_cpp`, `sql_data`, `system_ops`). Enforces strict `< 150 MiB` per-adapter VRAM guard and Single Active Adapter invariant to respect the $\le 4,812\text{ MiB}$ hardware ceiling.
- **Multimodal Vision Token Optimization**: Exact Gemma 4 formula calibration ($T = N_w \times N_h + N_h + 2$). Uses dynamic quadratic aspect-preserving patch budgeting to downsample raw screenshots from 4,838 tokens to 233 tokens ($20.8\times$ compression) within the 256 token budget.

### 8.4. Zero-Test-Folder Architecture
- The living harness is completely self-contained. All contract verification, isolation guards, and recovery loops are integrated directly into first-party probes in `verify_harness_integrity.py`.
- External `tests/` directories serve only as transitional developmental scaffolding; in production, `verify_harness_integrity.py --standalone` natively certifies the OS in under 3 seconds without loose pytest dependencies.

---

## 9. Documentation Hub

Comprehensive, single-source-of-truth documentation is consolidated in the [`docs/`](./docs/README.md) directory:

* 📚 **[Documentation Index & Quickstart (docs/README.md)](./docs/README.md)**: Getting started, common CLI commands, and system invariants.
* 🏛️ **[System Architecture & Execution Flow (docs/architecture.md)](./docs/architecture.md)**: C4 diagrams, 5 closed-loop phases, 28-plugin catalog, and filesystem layout.
* 🔬 **[Master Research Audit & ADRs (docs/research.md)](./docs/research.md)**: 62 chronological research papers, paradigms (Eras 1–8), and Architectural Decision Records.
* 🧪 **[Verification, Benchmarks & Self-Evolution (docs/verification.md)](./docs/verification.md)**: 10 in-process contract verification suites, benchmarks, and scheduled cron jobs.
* 🔌 **[Substrates, Sidecars & Integrations (docs/integrations.md)](./docs/integrations.md)**: FastMCP Open-Notebook RAG, Port 8139 Vision Sidecar, CUA Desktop driver, and Google ADK.

