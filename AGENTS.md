# AGENTS.md — AI Agent Operating Standard & Repository Orientation

> **Target Audience**: AI Coding Agents (Google Antigravity, Claude Code, OpenAI Codex, Cursor, Windsurf, Jules)  
> **Project**: Hermes Agent OS & Living Verification Harness  
> **Status**: **100% Complete & Production Certified** (All 17 In-Process Capability Contracts Passing)  
> **Local Runtime**: Fedora Distrobox (`ws-hermes`), NVIDIA RTX 3050 (6GB VRAM), Local `llama-server` (Port 8138)

---

## 1. Welcome & Repository Identity

Welcome, Agent. You are operating inside the **Hermes Agent OS** repository.

Hermes Agent OS is a local-first, autonomous agent operating system that elevates lightweight open-weight models (such as `Gemma-4-4B` and `Gemma-3-4B`) to production parity with frontier enterprise systems. It provides deterministic System-2 decomposition, hardware-bounded VRAM management, in-process contract verification gates, and continuous in-the-loop learning.

**Crucial Note**: This document (`AGENTS.md`) is written for **YOU** (the external AI assistant pair-programming on this repository). It guides how you must navigate, edit, and verify this codebase. For the internal cognitive identity of Hermes itself, see [`SOUL.md`](file:///var/home/imshubhamsocial/Projects/Workspace/Personal/hermes/.hermes/SOUL.md) and [`docs/architecture.md`](file:///var/home/imshubhamsocial/Projects/Workspace/Personal/hermes/docs/architecture.md).

---

## 2. Repository Anatomy & Directory Map

The repository is organized into a clean, minimal root with all runtime execution state encapsulated inside `.hermes/`:

```
/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes/
├── AGENTS.md                  # <-- You Are Here: Definitive operating standard for AI coding agents
├── README.md                  # Project overview, quickstart, and feature matrix
├── Makefile                   # Unified developer targets (sys-deps, py-deps, node-deps)
├── pyproject.toml             # Single canonical Python manifest (PEP 621 dependencies, ruff, pytest)
├── package.json               # Node.js devDependencies (ast-grep, Biome, prettier, pyright)
├── requirements.txt           # Minimal pointer (-e .[dev,benchmark,vision]) linking to pyproject.toml
├── setup.sh                   # Environment provisioning and first-time setup script
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
│   ├── plugins/               # 28 capability plugins (see docs/architecture.md for catalog)
│   ├── rules/                 # Inferred behavioral invariants & system prompt rules
│   ├── scripts/               # Operational utility scripts
│   ├── SOUL.md                # 176-line cognitive system identity prompt
│   └── config.yaml            # Master configuration for models, plugins, and gateways
│
├── .local/                    # Container $HOME/.local user environment (auto-created by distrobox)
│   ├── bin/                   # System runtime binaries (llama-server, tirith, uv, hermes symlink)
│   └── lib/                   # GGML CUDA/CPU libraries and python3.13 site-packages
│
└── ~/.local/share/chezmoi/    # Chezmoi dotfiles git repository tracking private_dot_hermes/
```

---

## 3. The 8 Golden Laws for AI Agents Working in This Repository

Every plan, code change, or terminal command executed by an AI agent must strictly comply with these 8 non-negotiable laws:

### Law 1: Surgical Edits & The Ponytail 7-Rung YAGNI Ladder
* Keep all code diffs surgical. Respect the **Karpathy U12 3x Diff Limit** (never expand a 5-line fix into a 50-line abstraction).
* Never invent custom wrapper classes, helper abstractions, or single-method factories when Python standard library functions (e.g. `pathlib.Path`, `sqlite3`, `json`) suffice.

### Law 2: Physical Hardware & VRAM Ceilings
* The host environment has an **NVIDIA GeForce RTX 3050 Laptop GPU (6,144 MiB physical VRAM)**.
* Active GPU allocation must **never exceed 4,812 MiB**.
* All vector embeddings (`fastembed`, BGE-small, Gemma embeddings) and AST parsing **must execute 100% on CPU RAM**. Never offload embeddings to CUDA.

### Law 3: Zero Test Rule Pollution
* When testing `/loop learn` or `AutonomousLearner`, tests **must never write permanent rule files** into `.hermes/rules/` or `~/.hermes/rules/`.
* Always use `tempfile.TemporaryDirectory()` for tests, or explicitly clean up any synthetic test rules (`rule_*test_pre*.md`) immediately after assertion.

### Law 4: Isolated Container Environment (`ws-hermes`) & Zero Host Pollution
* Hermes runs in a dedicated Distrobox container named `ws-hermes` with `--home /var/home/imshubhamsocial/Projects/Workspace/Personal/hermes` to emulate an isolated, fresh PC setup.
* Inside `ws-hermes`, `$HOME` is the workspace root itself; thus `$HOME/.hermes` resolves directly to `./.hermes` and `$HOME/.local/bin` resolves to `./.local/bin`.
* **Host Home Invariant**: Never execute commands or generate files in the host home (`/var/home/imshubhamsocial`). The host environment must remain 100% clean and unpolluted.
* **Core Code vs `.local/bin` Invariant**: Never place prototype python scripts, experimental CLI wrappers, or alias symlinks into `.local/bin` (e.g. legacy `observer-gate` or `hypothesis-tree`). All agent features, verification gates, and AST checks belong canonically in `.hermes/plugins/` or `agent/core/`. The directory `.local/bin/` is strictly reserved for standard package executables (`pip`, `uv`), compiled daemon runtimes (`llama-server`, `tirith`), and the `hermes` CLI entrypoint.
* Always execute verification, tests, and agent commands inside the container via:
  ```bash
  distrobox enter ws-hermes -- <command>
  ```
* Config and rule synchronization: maintain strict parity between `./.hermes/` and the Chezmoi repository (`~/.local/share/chezmoi/private_dot_hermes/`).

### Law 5: Zero Root Pollution
* The workspace root must remain clean and minimal.
* **Never** create scratch markdown files, test dumps, or temporary directories in the workspace root.
* All documentation belongs in `docs/`. All runtime state belongs in `.hermes/`. Temporary files belong in `tmp/` or temporary directories.

### Law 6: In-Process Verification First
* Before declaring any task complete, run the corresponding in-process verification harnesses in `.hermes/bin/`.
* Ensure that all 10 contracts exit with code 0.

### Law 7: Two-Strike Tabu Rule
* If an edit or command fails two consecutive times, do **not** blindly retry the same approach.
* Immediately halt, revert the failing changes via git or backup (`.bak`), and re-diagnose the root cause.

### Law 8: Canonical Packaging via `pyproject.toml`
* Do not create separate requirements files or ad-hoc pip dependencies.
* All Python dependencies, test dependencies, and tools are declared canonically in [`pyproject.toml`](file:///var/home/imshubhamsocial/Projects/Workspace/Personal/hermes/pyproject.toml).

---

## 4. Agent Verification & Diagnostic Commands

Whenever verifying your changes or testing environment health, execute these commands:

### Running Capability Contracts:
```bash
# Verify all 17 capability contracts via Makefile
make test

# Or run individual capability contracts directly from .hermes/contracts/
python3 .hermes/contracts/director.py
python3 .hermes/contracts/planner.py
python3 .hermes/contracts/autonomous_loop.py
python3 .hermes/contracts/contract_gate.py
python3 .hermes/contracts/self_learning.py
python3 .hermes/contracts/capability_monitoring.py
```

### Running Linters & Code Quality:
```bash
# Fast AST scan and formatting via Biome
npm run lint
npm run format

# Python linting via Ruff
ruff check .
```

### Checking System & GPU Health:
```bash
# Verify GPU VRAM headroom and system dependencies
hermes doctor
```

---

## 5. Where to Find In-Depth Documentation

For deeper architectural, theoretical, and operational details, refer to the consolidated guides in [`docs/`](file:///var/home/imshubhamsocial/Projects/Workspace/Personal/hermes/docs):

* 📚 **[`docs/README.md`](file:///var/home/imshubhamsocial/Projects/Workspace/Personal/hermes/docs/README.md)** — Master documentation index and CLI command cheat sheet.
* 🏛️ **[`docs/architecture.md`](file:///var/home/imshubhamsocial/Projects/Workspace/Personal/hermes/docs/architecture.md)** — C4 architecture diagrams, 5 runtime phases, 28-plugin catalog, and hardware invariants.
* 🔬 **[`docs/research.md`](file:///var/home/imshubhamsocial/Projects/Workspace/Personal/hermes/docs/research.md)** — Master chronological research register (62 items & 8 ADRs).
* 🧪 **[`docs/verification.md`](file:///var/home/imshubhamsocial/Projects/Workspace/Personal/hermes/docs/verification.md)** — Detailed specification of all 10 in-process harnesses, benchmarks, and cron daemons.
* 🔌 **[`docs/integrations.md`](file:///var/home/imshubhamsocial/Projects/Workspace/Personal/hermes/docs/integrations.md)** — FastMCP Open-Notebook RAG, Port 8139 Vision Sidecar, CUA Desktop driver, and Google ADK.
