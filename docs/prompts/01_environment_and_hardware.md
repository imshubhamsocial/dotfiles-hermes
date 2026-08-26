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
* **Status**: **567/567 PASS (100%)** in $28.59\text{s}$ when executed inside `ws-hermes`.

---

## 3. Local Inference Engine (`llama-server`)

* **Self-Contained Launcher**: `~/.local/bin/llama-server` (or `bin/start_server_daemon.sh`).
* **Endpoint**: `http://127.0.0.1:8138/v1`
* **Target Model**: Gemma-4-E4B-it Q4_K_M (`assets/gguf/gemma-4-E4B-it-Q4_K_M.gguf`).
* **Speculative Drafter**: MTP Q4_0 (`assets/MTP/mtp-gemma-4-E4B-it-Q4_0.gguf`).
* **Active Acceleration Flags**:
  * `--port 8138 --host 127.0.0.1 -c 65536 -ngl 99`
  * `--model-draft assets/MTP/mtp-gemma-4-E4B-it-Q4_0.gguf --spec-draft-n-max 3` (3 tokens ahead MTP speculative decoding)
  * `--cache-type-k q4_0 --cache-type-v q4_0` (64k context in ~1.25 GB VRAM)
  * `--parallel 4 --slots -s 4` (Parallel multi-turn slot isolation)
  * `--jinja` (Gemma native tool-calling DSL)
* **Measured Memory Footprint**: **$3,797\text{ MiB}$ VRAM** ($>2.3\text{ GB}$ safe headroom).
* **Generation Speed**: **$48.0\text{ tok/s}$** with MTP drafter enabled ($1,350\text{--}1,690\text{ tok/s}$ prompt prefill).

---

## 4. Repository Structure & Canonical Upstream Layout

All paths in scripts and configuration MUST be **100% relative** to repository root or resolve against `$HOME`:

```
hermes/
├── bin/                                # Standalone CLI executables, observer gates & daemon scripts
│   ├── observer_gate.py                # Pre-commit 6-point AST verification gate
│   ├── visual_arbiter.py               # Headless Playwright WebGL kinematic validator
│   ├── verify_harness_integrity.py     # Master capability audit & contract verification runner
│   └── start_server_daemon.sh          # Local llama-server daemon launcher
│
├── ~/.hermes/                          # Canonical Upstream Hermes Runtime Substrate
│   ├── config.yaml                     # Hardware configurations, context engine & plugin toggles
│   ├── rules/                          # Two-tier immutable kernel & project behavioral standards
│   ├── skills/                         # OpenSkills progressive context stubs (L0/L1/L2)
│   ├── bin/                            # Self-contained runtime binaries & execution bridges
│   ├── plugins/                        # Native standalone plugins & lifecycle adapters
│   │   ├── observer_gate/              # Pre-commit AST syntax & phantom citation interceptor
│   │   ├── recirculation_adapter/      # Google DeepMind Recirculation System-2 prefill (+20% lift)
│   │   ├── reflective_learner_adapter/ # Google ADK 2.0 TaskDAG SQLite /learn feedback loop
│   │   └── synergy_bus_adapter/        # Unified reactive execution & memory event bus
│   └── hermes-agent/                   # Upstream Hermes Agent engine
│       ├── agent/core/                 # 16 in-tree cognitive OS subsystems
│       └── plugins/
│           ├── context_engine/         # OpenViking 3-tier VFS (<4k token sliding compaction)
│           └── memory/                 # OpenCode-Mem pure CPU ONNX BGE vector store
│
├── tests/                              # Comprehensive test suites & contract spikes
│   ├── harness_contracts/              # 567 passed contract tests verifying all capabilities
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
