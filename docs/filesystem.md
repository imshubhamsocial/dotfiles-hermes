# Filesystem Architecture & Directory Layout

This document explains the project folder structure in plain, easy-to-understand terms.

---

## 1. High-Level Folder Tree

```
hermes/
├── .hermes/                       # Live symlink to ~/.hermes (Runtime Home)
│   ├── plugins/                   # Native Hermes Plugins v1 extensions (16 plugins)
│   ├── skills/                    # Modular skills library & execution routines
│   ├── rules/                     # Behavioral directives & cognitive bounds
│   ├── memories/                  # SQLite WAL database & persistent knowledge cards
│   ├── bin/                       # Executable CLI scripts & self-evolution tools
│   ├── profiles/                  # Agent persona definitions (coder, architect, etc.)
│   ├── SOUL.md                    # Core persona & cognitive architecture definition
│   ├── config.yaml                # Core runtime configuration & enabled plugins
│   └── hermes-agent/              # Isolated upstream NousResearch engine clone & venv
│
├── .local/share/chezmoi/          # Dotfiles source repository (tracked by Git)
│   ├── private_dot_hermes/        # Chezmoi source for ~/.hermes
│   ├── tests/                     # Test suites mirror
│   ├── pyproject.toml             # Python package dependencies & entry points
│   └── setup.sh                   # Automated one-click installation & provisioning
│
├── docs/                          # Architecture, benchmark, and workflow guides
│   ├── test.md                    # Evaluation metrics & benchmarking guide
│   ├── filesystem.md              # Directory structure explanation (this file)
│   ├── defaults.md                # System invariants, timeouts, and flags
│   ├── components.md              # Catalog of all tools, libraries, and submodules
│   └── flow.md                    # End-to-end component interaction flow
│
└── tests/                         # Complete test suite (unit, plugin, and contract tests)
```

---

## 2. Directory Purpose in Plain English

### `plugins/` (The Extension Store & Cognitive Capabilities)
Self-contained packages (`agent_os`, `adk_orchestrator`, `nemo_guardrails`, `reflective_learner_adapter`, `mcp_tools`, etc.) that add new capabilities without modifying core engine files. Each plugin has a `plugin.yaml` manifest and standard Python entry points.

### `skills/` (The Dynamic Procedures)
Modular task guides and operational protocols loaded just-in-time when specific task keywords or execution domains require them.

### `bin/` (The Executables & Self-Evolution Tools)
Scripts you can run directly from the terminal, such as `hypothesis_tree.py` for multi-branch hypothesis exploration or diagnostics.

### `memories/` (The Long-Term Memory)
SQLite database in WAL journal mode and memory markdown cards preserving episodic memories, trajectory traces, and learned behavioral invariants.

### `tests/` (The Safety Net)
A comprehensive suite of tests ensuring that no code change breaks backward compatibility, plugin contracts, or safety invariants.

### `docs/` (The Manual)
Clear references explaining how every piece works, how to benchmark it, and how to debug issues.

