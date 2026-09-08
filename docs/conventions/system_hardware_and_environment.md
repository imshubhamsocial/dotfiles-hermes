# 01. Environment, Hardware Envelope & Repository Structure

> **Authoritative Context**: Master onboarding & runtime context for autonomous agent execution  
> **Target Substrate**: Fedora Kinoite Host + `ws-hermes` Distrobox Substrate

---

## 1. Physical Hardware Envelope & Safety Guards

All code execution, model configurations, and test runners must respect strict physical hardware bounds:

* **Host Machine**: Fedora Kinoite (OSTree / Silverblue Immutable Root).
* **GPU**: Single NVIDIA RTX 3050 Laptop GPU (**6 GB GDDR6 VRAM**, Compute Capability 8.6).
* **VRAM Safety Ceiling**: **$\le 4,812\text{ MiB}$** (Never exceed to prevent Linux OOM-killer).
* **System RAM**: 16 GB Host RAM.
* **Storage Standard**:
  * Persistent repository: `~/Projects/Workspace/Personal/hermes`
  * Upstream Hermes runtime: `~/.hermes/`
  * High-frequency writes, SQLite WAL databases, trajectories & test scratchpads: `/dev/shm` (RAMDisk).
  * Storage fragmentation prevention: `chattr +C` (NOCOW) for database directories on Btrfs.

---

## 2. Execution Container & Testing Rule (`ws-hermes`)

> [!IMPORTANT]
> **All contract test runs, Playwright tests, and Python commands MUST be executed inside the `ws-hermes` distrobox container.**  
> Running `pytest` or `python3` directly on the host will fail due to missing containerized toolchains.

* **Primary Substrate**: `ws-hermes` container with CUDA, Python 3.13.15, Pytest 9+, Playwright, Tree-sitter, and FastEmbed.
* **Command Wrapper**:
  ```bash
  distrobox enter ws-hermes -- python3.13 -m pytest tests/harness_contracts/ -q
  ```
* **Status**: **602/602 PASS (100%)** when executed inside `ws-hermes` or native host.

---

## 3. Local Inference Engine (`llama-server`)

* **Self-Contained Launcher**: `~/.local/bin/llama-server` (or `.hermes/scripts/start_server_daemon.sh`).
* **Endpoint**: `http://127.0.0.1:8138/v1`
* **Standard Model Cache**: `~/.cache/huggingface/hub/models--bartowski--gemma-4-E4B-it-GGUF/snapshots/main/`
* **Target Model**: Gemma-4-E4B-it Q4_K_M (`gemma-4-E4B-it-Q4_K_M.gguf`).
* **Speculative Drafter**: MTP Q4_0 (`mtp-gemma-4-E4B-it-Q4_0.gguf`).
* **Active Acceleration Flags**:
  * `--port 8138 --host 127.0.0.1 -c 131072 -ngl 99`
  * `--model-draft .../mtp-gemma-4-E4B-it-Q4_0.gguf --spec-draft-ngl 99 --spec-draft-n-max 3` (3 tokens ahead MTP speculative decoding)
  * `--cache-type-k q4_0 --cache-type-v q4_0` (65k context per slot in ~1.25 GB VRAM)
  * `-np 2` (2 parallel slots isolated context)
  * `--flash-attn on --jinja` (Gemma native tool-calling DSL)
  * `--temp 1.0 --top-p 0.95 --top-k 64` (Official Google Gemma-4 sampling distribution)
  * `taskset -c 0-11` (P-Core CPU affinity pinning on 13th Gen Intel)
* **Measured Memory Footprint**: **$4,234\text{ MiB}$ VRAM** (safe below $4,812\text{ MiB}$ ceiling).
* **Generation Speed**: **$28\text{--}48\text{ tok/s}$** with MTP drafter enabled ($1,410\text{ tok/s}$ prompt prefill).

---

## 4. Repository Structure & Canonical Upstream Layout

All paths in scripts and configuration MUST be **100% relative** to repository root or resolve against `$HOME`:

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
│   ├── bin/                            # Standalone verification & gate scripts (observer_gate.py, etc.)
│   ├── plugins/                        # Native standalone plugins (agent_os, cog_verifier, symbol_index)
│   ├── src/hermes_core/                # Cognitive OS subsystems & Python engine sources
│   └── hermes-agent/                   # Upstream Hermes Agent engine
│
└── tests/                              # Comprehensive test suites & contract spikes
    ├── harness_contracts/              # 602 passed contract tests verifying all capabilities
│   └── oracle_references/              # Gold-standard baseline benchmarks
│
├── docs/                               # Professional documentation hierarchy
│   ├── roadmaps/                       # Architectural roadmaps (Roadmaps 1-4 completed)
│   ├── operations/                     # Operational guides & environment context
│   └── prompts/                        # System prompts & onboarding context
│
├── pyproject.toml                      # Package build configuration
└── packages.json                       # System package manifests
```
