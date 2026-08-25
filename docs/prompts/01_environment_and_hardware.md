# 01. Environment, Hardware Envelope & Repository Structure

> **Authoritative Context**: For autonomous execution via OpenAI Codex on Host / `ws-hermes`  
> **Target Substrate**: Fedora Kinoite Host + `ws-hermes` Distrobox Substrate

---

## 1. Physical Hardware Envelope & Safety Guards

All code execution, model configurations, and test runners must respect strict physical hardware bounds:

* **Host Machine**: Fedora Kinoite (OSTree / Silverblue Immutable Root).
* **GPU**: Single NVIDIA RTX 3050 Laptop GPU (**6 GB GDDR6 VRAM**, Compute Capability 8.6).
* **VRAM Safety Ceiling**: **$\le 4,800\text{ MiB}$** (Never exceed to prevent Linux OOM-killer).
* **System RAM**: 16 GB Host RAM.
* **Storage Standard**:
  * Persistent source code: `/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes`
  * High-frequency writes, SQLite WAL databases, trajectories & test scratchpads: `/dev/shm` (RAMDisk).
  * Storage fragmentation prevention: `chattr +C` (NOCOW) for database directories on Btrfs.

---

## 2. Distrobox Container Environment (`ws-hermes`)

* **Primary Substrate**: `ws-hermes` container with CUDA 13, Python 3.13, Pytest 9+, Playwright, Tree-sitter, and FastEmbed.
* **Container Invocation**:
  ```bash
  distrobox enter ws-hermes -- <command>
  ```
* **Python Executable**: Use `python3.13` inside `ws-hermes`.
* **Testing Command**:
  ```bash
  distrobox enter ws-hermes -- pytest tests/harness_contracts/ -q
  ```

---

## 3. Local Inference Engine (`llama-server`)

* **Self-Contained Launcher**: `~/.local/bin/llama-server` (or `bin/start_server_daemon.sh`).
* **Endpoint**: `http://127.0.0.1:8138/v1`
* **Target Model**: Gemma-4-E4B-it Q4_K_M (`assets/gguf/gemma-4-E4B-it-Q4_K_M.gguf`).
* **Speculative Drafter**: MTP Q4_0 (`assets/MTP/mtp-gemma-4-E4B-it-Q4_0.gguf`).
* **Active Acceleration Flags**:
  * `--flash-attn on` (Fused SRAM attention)
  * `--model-draft ... --spec-draft-n-max 3` (3 tokens ahead MTP speculative decoding)
  * `--cache-type-k q4_0 --cache-type-v q4_0 -c 65536` (64k context in ~1.25 GB VRAM)
  * `--threads 6 --threads-batch 6 --cpu-range 0-11 --cpu-strict 1` (Core pinning)
  * `--jinja` (Gemma native tool-calling DSL)
* **Measured Memory Footprint**: **$3,745\text{ MiB}$ VRAM** ($>2.4\text{ GB}$ safe headroom).

---

## 4. Repository Structure & Relative Paths

All paths in scripts and configuration MUST be **100% relative** to repository root or resolve against `$HOME`:

```
hermes/
├── assets/                     # Model weights (tracked in Chezmoi Git-LFS)
│   ├── gguf/                   # Main base models (*.gguf)
│   └── MTP/                    # Multi-Token Prediction draft heads
├── bin/                        # Standalone executables, daemon scripts, observer gates
│   ├── llama/                  # Self-contained llama-server binaries and CUDA libs
│   ├── start_server_daemon.sh  # Relative daemon launcher
│   ├── observer_gate.py        # 6-point pre-commit AST verification gate
│   └── visual_arbiter.py       # Playwright WebGL kinematic validator
├── docs/                       # Architectural documentation and roadmaps
│   ├── roadmaps/active/        # Active milestone plans and research archive
│   └── prompts/                # Codex guidance and execution prompts
├── hermes_core/ (or src/)      # Core Python packages for agent OS subsystems
├── tests/                      # Contract test suites and benchmarks
│   ├── harness_contracts/      # Phase-specific regression and contract tests
│   └── master_leaderboard_runner.py
└── README.md                   # Master repository specification
```
