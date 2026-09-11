# Filesystem Architecture & Directory Layout (Era 10)

This document explains the project folder structure in plain, easy-to-understand terms for both human engineers and autonomous agents.

---

## 1. High-Level Directory Tree

```
/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes/
├── AGENTS.md                  # Master operating standard & architectural codex for all agents
├── Plan.md                    # Active multi-phase architectural plan
├── Summary.md                 # Living engineering certification ledger
├── README.md                  # High-level overview, quick start, and feature matrix
├── Makefile                   # Unified developer entry point (test, exam, sync, server)
├── hermes-pack.yaml           # Declarative manifest tracking all 26 active plugins
├── pyproject.toml             # Python packaging, dependencies, and pytest configuration
│
├── .hermes/                   # Core Hermes Agent OS runtime directory (symlinked to ~/.hermes)
│   ├── plugins/               # 26 native capability plugins (see components.md)
│   │   ├── antigravity_bridge # Google AGY 2.0 Generative UI artifacts, thought signatures, A2A
│   │   ├── trajectory_recorder# SQLite WAL trajectory & session observability engine
│   │   ├── bpe_workspace      # Belief-Progress-Experience state workspace (EvoHarness-RL)
│   │   ├── nemo_guardrails    # NVIDIA NeMo Guardrails Colang 2.0 execution rails
│   │   ├── adk_orchestrator   # Google ADK 2.8+ TaskDAG orchestration and Swarm handoffs
│   │   └── ...                # 21 additional specialized capability plugins
│   ├── bpe/                   # Active BPE state files (belief.md, progress.md)
│   ├── cache/                 # SQLite WAL databases (trajectories.db, state.db)
│   ├── evolution/             # Spec-kit self-evolution hypotheses and benchmark baselines
│   ├── memories/              # Long-term semantic, conceptual, and experiential memory cards
│   ├── tests/                 # 266-test verification suite (contracts, safety, agent, tools, core)
│   ├── docs/                  # Architectural specs, C4 diagrams, and user manuals
│   ├── SOUL.md                # 176-line cognitive system identity prompt
│   └── config.yaml            # Master runtime configuration for plugins and gateways
│
└── .local_archived/share/chezmoi/ # Chezmoi dotfiles tracking root (git remote origin/master)
```

---

## 2. Directory Purpose in Plain English

### `plugins/` (The Cognitive Capabilities & Framework Bridges)
Self-contained modules that add capabilities to Hermes without touching upstream code. Each plugin contains a `plugin.yaml` manifest and standard Python entry points. Era 10 features 26 active plugins covering security, execution, memory, planning, and frontier laboratory bridges.

### `bpe/` (The Live Working Memory)
Implements the Belief-Progress-Experience workspace:
- `belief.md`: Current assumptions, verified ground truths, and environmental invariants.
- `progress.md`: Subgoal DAG tracking completed milestones and active execution steps.

### `cache/` (The Persistent Trajectory & Observability Store)
Contains `trajectories.db` (SQLite in WAL mode) which records every turn, System-2 reasoning trace, tool invocation, exit code, and test status with SWE-agent observation windowing (head/tail 25 lines).

### `evolution/` (The Self-Referential Engine)
Stores hypothesis contracts (`hypotheses/*.json`) and historical test performance baselines (`baselines/`). Used by the Meta-Harness outer loop to continuously test and refine harness tools and prompts.

### `memories/` (The Long-Term Episodic Vault)
Preserves cross-session knowledge cards, user preferences, and verified architectural patterns.

### `tests/` (The Verification Safety Net)
Organized into 5 functional categories:
- `contracts/`: AGY bridge, thought signatures, ledgers, A2A, entropy rails, PRMs.
- `safety/`: NeMo guardrails, AgentShield security, role enforcer, observer gate.
- `agent/`: ADK orchestrator, trajectory recorder, domain fleet, DAG planner.
- `tools/`: FastMCP, Aider search-replace diffs, smolagents code actions.
- `core/`: Configuration, context budget manager, memory subsystems.

### `docs/` (The Technical Reference Library)
- `AGENTS.md`: The single source of truth for agent behavior and hardware invariants.
- `components.md`: Complete catalog of 26 plugins and upstream frameworks.
- `flow.md`: Turn lifecycle flow chart and diagnostic cheatsheet.
- `architecture/overview.md`: Litho C4 architecture specification.
