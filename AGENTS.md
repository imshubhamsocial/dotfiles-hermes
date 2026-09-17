# AGENTS.md — AI Agent Operating Standard & Repository Orientation

> **Target Audience**: AI Coding Agents (Google Antigravity, Claude Code, OpenAI Codex, Cursor, Windsurf, Jules)  
> **Project**: Hermes Agent OS & Living Verification Harness  
> **Status**: **Realigned Upstream Standard** (Pristine NousResearch Core, 4-Tier Architecture, Native Testbeds)  
> **Local Runtime**: Fedora Distrobox (`ws-hermes`), NVIDIA RTX 3050 (6GB VRAM), Local `llama-server` (Port 8138)

---

## 1. Welcome & Repository Identity

Welcome, Agent. You are operating inside the **Hermes Agent OS** repository.

Hermes Agent OS is a local-first, autonomous agent operating system that elevates lightweight open-weight models (such as `Gemma-4-E4B` and `Gemma-3-4B`) to production parity with frontier enterprise systems. It provides deterministic System-2 decomposition, hardware-bounded VRAM management, AST navigation, and continuous in-the-loop learning.

**Crucial Note**: This document (`AGENTS.md`) is written for **YOU** (the external AI assistant pair-programming on this repository). It guides how you must navigate, edit, and verify this codebase. For living operational status, see [`State.md`](file:///var/home/imshubhamsocial/Projects/Workspace/Personal/hermes/State.md). For realignment strategy, see [`Plan.md`](file:///var/home/imshubhamsocial/Projects/Workspace/Personal/hermes/Plan.md). For internal cognitive identity, see [`SOUL.md`](file:///var/home/imshubhamsocial/Projects/Workspace/Personal/hermes/.hermes/SOUL.md) and [`docs/architecture.md`](file:///var/home/imshubhamsocial/Projects/Workspace/Personal/hermes/docs/architecture.md).

---

## 2. Repository Anatomy & Directory Map

The repository is organized into a clean, minimal root with all runtime execution state encapsulated inside `.hermes/`:

```
hermes/ (workspace root)
├── AGENTS.md                  # <-- You Are Here: Definitive operating standard for AI coding agents
├── State.md                   # Living operational state, hardware health, and active research phases
├── Plan.md                    # 4-tier clean architecture realignment plan & migration log
├── Evolution.md               # Master theoretical evolution and autonomous RSI roadmap
├── Mappings.md                # 1:1 legacy synthetic purge mapping against upstream architecture
├── README.md                  # Project overview, quickstart, and feature matrix
├── Makefile                   # Unified developer targets (sys-deps, py-deps, node-deps, test, doctor)
├── pyproject.toml             # Single canonical Python manifest (PEP 621 dependencies, ruff, pytest)
├── package.json               # Node.js devDependencies (ast-grep, Biome, prettier, pyright)
├── requirements.txt           # Minimal pointer (-e .[dev,benchmark,vision]) linking to pyproject.toml
│
├── docs/                      # Consolidated, single-source-of-truth documentation suite
│   ├── README.md              # Documentation index and quickstart guide
│   ├── architecture.md        # 4-Tier system architecture, C4 diagrams, upstream tool catalog
│   ├── research.md            # Master chronological research register (62 items & 8 ADRs)
│   ├── verification.md        # Real verification harnesses, compiler testbeds, and health checks
│   └── integrations.md        # FastMCP Open-Notebook, Port 8139 Vision, CUA, Antigravity Bridge
│
├── tests/                     # Isolated, self-contained git testbeds for prompt evaluations
│   ├── ast_grep_eval/         # AST pattern extraction and compilation testbed (sample_target.c)
│   ├── neovim_eval/           # Upstream C codebase patch and build evaluation
│   └── memory_eval/           # Cognitive memory retrieval and invariant rule evaluation
│
├── .hermes/                   # Complete encapsulated runtime substrate (mirrored to ~/.hermes)
│   ├── rules/                 # Inferred behavioral invariants & system prompt rules
│   ├── skills/                # Upstream Nous skills + domain capability skills
│   ├── memories/              # Long-term semantic memory and session reflections
│   ├── state.db               # SQLite WAL operational state database
│   ├── SOUL.md                # Cognitive system identity prompt
│   └── config.yaml            # Master configuration for models, tools, and gateways
│
├── .local/                    # Container $HOME/.local user environment (auto-created by distrobox)
│   ├── bin/                   # System runtime binaries (llama-server, tirith, uv, hermes symlink)
│   └── lib/                   # GGML CUDA/CPU libraries and python3.13 site-packages
│
└── ~/.local/share/chezmoi/    # Chezmoi dotfiles git repository tracking pure text dotfiles
```

---

## 3. The 12 Golden Laws for AI Agents Working in This Repository

Every plan, code change, or terminal command executed by an AI agent must strictly comply with these 12 non-negotiable laws:

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
* Hermes runs in a dedicated Distrobox container named `ws-hermes` with its home mapped to the workspace root directory (`--home <workspace_dir>`) to emulate an isolated, fresh PC setup.
* Inside `ws-hermes`, `$HOME` is the workspace root itself; thus `$HOME/.hermes` resolves directly to `./.hermes` and `$HOME/.local/bin` resolves to `./.local/bin`.
* **Host Home Invariant**: Never execute commands or generate files in the host user's home directory. The host environment must remain 100% clean and unpolluted.
* **Core Code vs `.local/bin` Invariant**: Never place prototype python scripts, experimental CLI wrappers, or alias symlinks into `.local/bin` (e.g. legacy `observer-gate` or `hypothesis-tree`). Upstream Hermes engine code remains 100% pristine. Cognitive extensions belong canonically in `.hermes/rules/` or `.hermes/skills/`, and developer tooling is declared in `package.json` / `pyproject.toml`. The directory `.local/bin/` is strictly reserved for standard package executables (`pip`, `uv`), compiled daemon runtimes (`llama-server`, `tirith`), and the `hermes` CLI entrypoint.
* Always execute verification, tests, and agent commands inside the container via:
  ```bash
  distrobox enter ws-hermes -- <command>
  ```
* Config and rule synchronization: maintain strict parity between `./.hermes/` and the Chezmoi repository (`~/.local/share/chezmoi/private_dot_hermes/`).

### Law 5: Zero Root Pollution
* The workspace root must remain clean and minimal.
* **Never** create scratch markdown files, test dumps, or temporary directories in the workspace root.
* All documentation belongs in `docs/` (except master state/plans in root: `State.md`, `Plan.md`, `Evolution.md`, `Mappings.md`, `AGENTS.md`). All runtime state belongs in `.hermes/`. Temporary files belong in `tmp/` or temporary directories.

### Law 6: In-Process & Testbed Verification First
* Before declaring any task complete, verify daemon health (`hermes doctor`), code linting (`npm run lint`, `ruff check .`), and execute the task's corresponding testbed verification under `tests/` using `hermes --in <testbed>`.
* Ensure real compiler and test suite exit codes return 0.

### Law 7: Two-Strike Tabu Rule
* If an edit or command fails two consecutive times, do **not** blindly retry the same approach.
* Immediately halt, revert the failing changes via git or backup (`.bak`), and re-diagnose the root cause.

### Law 8: Canonical Packaging via `pyproject.toml`
* Do not create separate requirements files or ad-hoc pip dependencies.
* All Python dependencies, test dependencies, and tools are declared canonically in [`pyproject.toml`](pyproject.toml).

### Law 9: Strict Path Portability & Zero Machine Hardcoding
* **Absolute Invariant**: Never hardcode host filesystem paths, username paths (e.g., `/var/home/imshubhamsocial`), or workspace paths in code, contracts, scripts, cron configurations, or metadata.
* All paths must dynamically resolve via:
  - Python: `Path(__file__).resolve().parents[...]`, `os.environ.get("HERMES_HOME", ...)`, or `Path.home()`
  - Shell: `${WORKSPACE_ROOT:-$(pwd)}`, `${HERMES_HOME:-$HOME/.hermes}`, `${HOME}`

### Law 10: Unified Makefile Toolchain Authority
* Do not create or retain standalone setup scripts (`setup.sh`, `install.sh`).
* All developer, installation, provisioning, and verification workflows are governed exclusively through `Makefile` targets (`make install`, `make test`, `make exam`, `make doctor`).

### Law 11: Isolated Git Testbeds under `tests/` & Production TUI Mandate
* All prompt-driven capability evaluations and synthetic scenarios must reside in their own dedicated subfolder under `tests/` initialized as an independent Git repository (`git init .`).
* Testbeds must remain completely self-contained with zero artifact or state leakage into the parent repository.
* All prompt evaluations must be executed through the rich Hermes TUI (`hermes "<prompt>"` or `hermes --in <testbed_dir>`), launched in a dedicated terminal window (`konsole`) via `distrobox-host-exec`, strictly adhering to the autonomous `/loop` paradigm.
* **Host vs Container Execution Rule**: Hermes and the testbeds execute inside `ws-hermes`. To open a GUI `konsole` window from inside the container, dispatch via `distrobox-host-exec`:
  ```bash
  distrobox-host-exec systemd-run --user --unit=hermes-<name>-goal \
    --setenv=WAYLAND_DISPLAY="wayland-0" \
    --setenv=DISPLAY=":0" \
    --setenv=XDG_RUNTIME_DIR="/run/user/$(id -u)" \
    konsole --separate -e distrobox enter ws-hermes -- /bin/bash <path_to_testbed_script>
  ```

### Law 12: Autonomous Prompting Authority (`/goal` & `/loop` Synergy)
* **Zero Casual/Ad-Hoc Prompting Mandate**:
  Never issue raw, single-turn prompts, informal requests, or open-ended instructions to Hermes without autonomous harness controls. Hermes is an autonomous System-2 Agent OS, not a stateless chat assistant. Driving Hermes without explicit goal boundaries and loop harnesses wastes compute tokens, induces premature stopping, generates hallucinated syntax breaks, and fails to engage upstream reasoning capabilities.
* **The `/goal` Autonomous Contract Standard**:
  Every task, evaluation, or bug-fix prompt dispatched to Hermes must be structured as an explicit `/goal` contract adhering to the NousResearch community standard:
  ```text
  /goal <Objective statement and tactical instructions>
  outcome: <Deterministic, observable end-state upon completion>
  verify: <Executable machine check command that must exit 0, e.g. ninja -C build && ./test.sh>
  constraints: <Negative constraints, e.g. surgical diffs, 2-strike tabu rule, zero root pollution>
  boundaries: <Confined filesystem paths, e.g. ./subsystem/src/>
  ```
  The agent is strictly prohibited from declaring success or halting until the `verify:` command returns exit code 0.
* **The `/loop` Continuous Execution & Learning Cycle**:
  - All multi-step workflows must execute within the autonomous `/loop` paradigm:
    $$\text{Substrate Recon} \longrightarrow \text{Hypothesis DAG} \longrightarrow \text{Surgical Diff} \longrightarrow \text{Compiler Gate} \longrightarrow \text{Test Verification} \longrightarrow \text{Invariant Distillation}$$
  - **Closed-Loop Distillation (`/loop learn` / `/learn`)**: Every successfully verified goal resolution must conclude with `/loop learn` (or `/learn` in the interactive TUI) to extract discovered build commands, tool caveats, and architectural invariants into `.hermes/rules/` and long-term memory.
* **Community & Production Parity**:
  Leading developers and frontier autonomous agent communities operate Hermes exclusively through this combined `/goal` + `/loop` paradigm. All evaluation scripts (`run_eval.sh`), launcher commands, and interactive developer sessions in this repository must enforce this standard.

---

## 4. Agent Verification & Diagnostic Commands

Whenever verifying your changes, managing daemons, or running testbeds, execute these commands:

### 1. Starting / Verifying Local LLM Server (Port 8138):
```bash
# If stopped, launch llama-server daemon:
systemd-run --user --unit=hermes-llama-server $HOME/.local/bin/llama-server

# Verify daemon status & health
curl -s http://localhost:8138/health
curl -s http://localhost:8138/slots | jq .

# Verify Hermes environment & tools
hermes doctor

# Check GPU VRAM allocation (must remain <= 4,812 MiB)
nvidia-smi --query-gpu=memory.used,memory.total --format=csv
```

### 2. Running Linters & Code Quality:
```bash
# Python linting via Ruff
ruff check .
```

### 3. Launching & Monitoring Isolated Testbed Evaluations:
```bash
# Launch Neovim Phase 2 evaluation in dedicated Konsole window:
distrobox-host-exec systemd-run --user --unit=hermes-neovim-goal \
  --setenv=WAYLAND_DISPLAY="wayland-0" \
  --setenv=DISPLAY=":0" \
  --setenv=XDG_RUNTIME_DIR="/run/user/$(id -u)" \
  konsole --separate -e distrobox enter ws-hermes -- /bin/bash /var/home/imshubhamsocial/Projects/Workspace/Personal/hermes/tests/neovim_eval/run_eval.sh

# Monitor evaluation service status
distrobox-host-exec systemctl --user status hermes-neovim-goal.service

# Stream evaluation logs in real time
distrobox-host-exec journalctl --user -u hermes-neovim-goal.service -f
```

---

## 5. Where to Find In-Depth Documentation

For deeper architectural, theoretical, and operational details, refer to the consolidated guides:

* 📊 **[`State.md`](State.md)** — Living operational state, hardware health, active testbeds, and blockers.
* 🗺️ **[`Plan.md`](Plan.md)** — 4-Tier clean architecture realignment plan and execution log.
* 📚 **[`docs/README.md`](docs/README.md)** — Master documentation index and CLI command cheat sheet.
* 🏛️ **[`docs/architecture.md`](docs/architecture.md)** — 4-Tier system architecture, C4 diagrams, and tool catalog.
* 🔬 **[`docs/research.md`](docs/research.md)** — Master chronological research register (62 items & 8 ADRs).
* 🧪 **[`docs/verification.md`](docs/verification.md)** — Multi-tier verification harness, compiler testbeds, and health checks.
* 🔌 **[`docs/integrations.md`](docs/integrations.md)** — FastMCP Open-Notebook RAG, Port 8139 Vision Sidecar, CUA Desktop driver, and Google ADK.
* 🧬 **[`Evolution.md`](Evolution.md)** — Master theoretical evolution and autonomous RSI roadmap.
* 🧭 **[`Mappings.md`](Mappings.md)** — Comprehensive 1:1 legacy synthetic purge mapping against upstream architecture.
