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

The inference engine runs locally via a highly optimized, patched `llama.cpp` server wrapper.

### 3.1. Hardware Allocation & Budget

| Component | Target Allocation | Measured Value | Operational Guardrail |
| :--- | :---: | :---: | :--- |
| **GPU Model** | NVIDIA RTX 3050 (Laptop) | 6,144 MiB VRAM | Hardware Ceiling |
| **Base Model Weights** | `gemma-4-E4B-it-Q4_K_M.gguf` | $\approx 2,450\text{ MiB}$ | 33 GPU Layers Offloaded (`-ngl 33`) |
| **KV Cache Allocation** | 65,536 Tokens in `q4_0` | $\approx 1,248\text{ MiB}$ | `--cache-type-k q4_0 --cache-type-v q4_0` |
| **Total Server Footprint** | Static In-Memory | **$\approx 3,745\text{ MiB}$** | **Budget: $\le 4,812\text{ MiB}$ (PASS)** |
| **VRAM Headroom** | Free for LoRA / Compute | **$\approx 2,399\text{ MiB}$** | Uncontended for Desktop & OS |

### 3.2. Patched llama-server Wrapper & Kernel Flags

The launcher wrapper is located at `~/.local/bin/llama-server` and starts the model with calibrated parameters:

```bash
/var/home/imshubhamsocial/Projects/Workspace/Personal/LLMs/llama.cpp/build/bin/llama-server \
    --model /var/home/imshubhamsocial/Projects/Workspace/Personal/LLMs/assets/gemma-4-E4B-it-Q4_K_M.gguf \
    --host 127.0.0.1 \
    --port 8138 \
    -ngl 33 \
    -c 65536 \
    --cache-type-k q4_0 \
    --cache-type-v q4_0 \
    --prompt-cache-all \
    --threads 6 \
    --metrics \
    --slot-save-path /dev/shm/llama_slots \
    --chat-template peg-gemma4
```

### 3.3. Prefix-Cache & KV-Cache Configuration

* **Prompt Cache All (`--prompt-cache-all`)**: Retains prefill state for static system prompt prefixes across multi-turn agent conversations.
* **Shared Memory RAMDisk Slots**: `/dev/shm/llama_slots` stores slot states in volatile RAM to reduce context-swapping latency to $<1\text{ms}$.
* **Context Length**: Fully allocated 64k token window (`-c 65536`) with quantized keys and values (`q4_0`) to prevent VRAM spikes.

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

## 5. Repository Structure

```
.
├── bin/                                # CLI executables, observer gates, and test runners
│   ├── hermes_os_cli.py                # Unified autonomous TaskDAG agent CLI
│   ├── observer_gate.py                # Pre-commit 6-point verification gate
│   ├── visual_arbiter.py               # Headless Playwright WebGL kinematic validator
│   └── verify_harness_integrity.py     # Master capability audit & contract verification runner
│
├── docs/                               # Professional documentation hierarchy
│   ├── README.md                       # Documentation navigation index
│   ├── roadmaps/                       # Architectural roadmaps (Roadmap 1 to 4)
│   ├── operations/                     # Operational guides, environment context & milestones
│   ├── research/                       # In-depth technical specifications & failure taxonomy
│   ├── knowledge/                      # Cognitive codebooks & orchestrator ledgers
│   ├── migration/                      # Container migration history
│   └── prompts/                        # System prompts & persona definitions
│
├── tests/                              # Comprehensive test suites & contract spikes
│   ├── harness_contracts/              # 309+ unit & contract tests verifying all capabilities
│   └── oracle_references/              # Gold-standard baseline benchmarks (Aquarium 3D, etc.)
│
├── packages.json                       # System package manifests for DNF, Python & Node CLI
├── setup.sh                            # 100% turnkey bootstrap installer script
└── pyproject.toml                      # Package configuration for hermes_core
```

---

## 6. Setup & Turnkey Portability

The harness is engineered to be 100% portable across machines (Fedora Kinoite/Silverblue, standard Fedora, or remote Linux servers) without hardcoded paths.

### Fresh Machine Bootstrap in 2 Commands:

```bash
# 1. Initialize and apply dotfiles & harness configurations
chezmoi init --apply <repo-url-or-path>

# 2. Run automated turnkey installer (DNF packages, Python toolchains, Playwright, Node CLIs)
./setup.sh
```

---

## 7. Operational Commands & CLI Guide

```bash
# Launch Hermes CLI with autonomous prompt execution
hermes chat -q "Decompose and build a 3D Solar System simulation in index.html" --yolo

# Run full harness capability and contract test audit
python3.13 bin/verify_harness_integrity.py

# Run all contract unit tests
python3.13 -m pytest tests/harness_contracts/ -v

# Run pre-commit observer gate manually on a file
python3.13 bin/observer_gate.py src/main.js
```

---

## 8. Documentation & Roadmaps

Detailed specifications are organized in the [`docs/`](./docs/README.md) directory:

* 🗺️ **[Roadmap 1: Master Autonomous Test Plan](./docs/roadmaps/roadmap1_master_test_plan.md)**: Baseline capabilities U1–U20.
* 🗺️ **[Roadmap 2: Agent OS Substrate](./docs/roadmaps/roadmap2_agent_os_substrate.md)**: 7-Layer substrate U21–U35.
* 🗺️ **[Roadmap 3: Production Graduation](./docs/roadmaps/roadmap3_production_graduation.md)**: Production parity U36–U44.
* 🗺️ **[Roadmap 4: Frontier Cognitive OS](./docs/roadmaps/roadmap4_frontier_cognitive_os.md)**: Memory graphs, NVIDIA Skill Lift, DeepMind Recirculation U45–U60.
