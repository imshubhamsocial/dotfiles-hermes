# Filesystem Architecture & Directory Layout

This document explains the project folder structure in plain, easy-to-understand terms.

---

## 1. High-Level Folder Tree

```
hermes/
├── .hermes/                       # Live symlink to ~/.hermes (Runtime Home)
│   ├── src/hermes_core/           # Single source of truth Python library (91 modules)
│   ├── plugins/                   # Official Hermes Plugins v1 extensions
│   ├── bin/                       # Executable CLI scripts and verification tools
│   ├── private_skills/            # Domain-specific agent skills
│   ├── profiles/                  # Agent persona definitions (coder, architect, etc.)
│   ├── state.db                   # SQLite WAL database for episodic memory
│   └── config.yaml                # Core runtime configuration
│
├── .local/share/chezmoi/          # Dotfiles source repository (tracked by Git)
│   ├── private_dot_hermes/        # Chezmoi source for ~/.hermes
│   ├── tests/                     # Test suites mirror
│   ├── pyproject.toml             # Python package dependencies & entry points
│   └── setup.sh                   # Automated one-click installation & provisioning
│
├── docs/                          # Architecture, benchmark, and workflow guides
│   ├── benchmark.md               # Evaluation metrics & benchmarking guide
│   ├── filesystem.md              # Directory structure explanation (this file)
│   ├── defaults.md                # System invariants, timeouts, and flags
│   ├── components.md              # Catalog of all tools, libraries, and submodules
│   └── flow.md                    # End-to-end component interaction flow
│
└── tests/                         # Complete test suite (620 tests)
    ├── harness_contracts/         # 39 contract test suites (602 unit tests)
    ├── runners/                   # Integration and live validation exam runners
    └── test_*.py                  # Domain-specific and plugin tests
```

---

## 2. Directory Purpose in Plain English

### `src/hermes_core/` (The Brain Engine)
Contains the core Python classes that power the agent. This includes the FastMCP server proxy, SQLite database layer, AST graph parser, and the multi-agent loop controller.

### `plugins/` (The Extension Store)
Self-contained packages (`quorum_audit`, `gepa_optimizer`, `observer_gate`, etc.) that add new capabilities without modifying core engine files. Each plugin has a `plugin.yaml` manifest and a `SKILL.md` instruction file.

### `bin/` (The Executables)
Scripts you can run directly from your terminal, such as `verify_harness_integrity.py` to audit system health or `web_grounding.py` for CLI search queries.

### `tests/` (The Safety Net)
A comprehensive suite of 620 tests ensuring that no code change breaks backward compatibility, token budgets, or hardware limits.

### `docs/` (The Manual)
Clear references explaining how every piece works, how to benchmark it, and how to debug issues.
