# Hermes Documentation Index

This directory contains the consolidated, single-source-of-truth documentation for Hermes Agent OS. All historical research, conventions, and architectural roadmaps have been directly incorporated into these operational guides and the living harness in `.hermes/`.

---

## Core Operational Guides

| Document | Purpose & Scope |
| :--- | :--- |
| 📘 **[AGENTS.md](../AGENTS.md)** | Root authoritative agent operating standard, The 8 Golden Laws, and 2-Tier testing hierarchy. |
| 🧩 **[components.md](./components.md)** | Ecosystem catalog of all upstream tools, official packages, and custom core subsystems. |
| ⚙️ **[defaults.md](./defaults.md)** | Enforced hardware budgets (RTX 3050 ≤ 4,812 MiB VRAM), token limits, and `llama-server` flags. |
| 🗂️ **[filesystem.md](./filesystem.md)** | Plain-English filesystem layout, runtime `.hermes/` substrate, and Chezmoi dotfile mapping. |
| 🔄 **[flow.md](./flow.md)** | End-to-end 5-phase turn execution pipeline and failure diagnosis matrix. |
| 🧪 **[test.md](./test.md)** | Two-tier benchmark methodology, Google envHarness validation, and verification commands. |
| 🗺️ **[roadmap.md](./roadmap.md)** | Active de-bloat, upstream package migration (D7), and execution priority tracker. |
| 🔬 **[evaluations/](./evaluations/)** | Architectural evaluations: [Google ADK](./evaluations/google_adk_evaluation.md) and [Primary Orchestration Selection](./evaluations/orchestration_selection.md). |
