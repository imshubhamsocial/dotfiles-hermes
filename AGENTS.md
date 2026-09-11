<!--
  Copyright 2026 Google LLC & DeepMind Advanced Agentic Coding
  Hermes Agent OS: Era 10 (v3.0.0-AGY-FRONTIER)
  Target Systems: Google DeepMind Antigravity 2.0 (AGY), Jules Cloud Agent, Local SLM Runtime (Gemma 4 4B / Qwen 2.5 3B)
  Hardware Boundary: NVIDIA RTX 3050 Laptop (<= 4,800 MiB VRAM Ceiling, CPU-Only ONNX Embeddings)
  Quality Standard: 100% Turnkey Determinism | 266/266 Green Tests | Zero Token Bloat | Single Entry Point
-->

# AGENTS.md — The Master Operating Standard & Architectural Codex for Hermes Agent OS

Welcome to **Hermes Agent OS** (`ws-hermes`). This document is the definitive orientation guide and engineering codex for both human engineers and autonomous AI agents (including Google Antigravity, Claude Code, OpenAI Codex, and local autonomous workers).

If you are a new agent entering this workspace or a human engineer reading this codebase for the first time: **Read this document thoroughly before mutating files, proposing plans, or executing commands.**

---

## Table of Contents
1. [System Mission & The Single Entry Point Mandate](#1-system-mission--the-single-entry-point-mandate)
2. [Frontier Research Foundations](#2-frontier-research-foundations)
3. [Physical Hardware Boundaries & VRAM Invariants](#3-physical-hardware-boundaries--vram-invariants)
4. [The 8 Golden Laws of Hermes OS](#4-the-8-golden-laws-of-hermes-os)
5. [Codebase Anatomy & Directory Map](#5-codebase-anatomy--directory-map)
6. [Master Plugin Roster (26 Active Plugins)](#6-master-plugin-roster-26-active-plugins)
7. [Subsystems Deep Dive](#7-subsystems-deep-dive)
   - [7.1. Antigravity 2.0 (AGY) Bridge & Generative Artifacts](#71-antigravity-20-agy-bridge--generative-artifacts)
   - [7.2. Cryptographic Thought Signatures](#72-cryptographic-thought-signatures)
   - [7.3. Hierarchical Rules Walker & Progressive Disclosure](#73-hierarchical-rules-walker--progressive-disclosure)
   - [7.4. Magentic-One Dual Ledgers & Stall Circuit Breaker](#74-magentic-one-dual-ledgers--stall-circuit-breaker)
   - [7.5. Anthropic Trinity & Claude Code Diff Engine](#75-anthropic-trinity--claude-code-diff-engine)
   - [7.6. Meta-Harness Outer Loop & MemRL Self-Evolution](#76-meta-harness-outer-loop--memrl-self-evolution)
   - [7.7. NVIDIA NeMo Rails & Shannon Entropy Filter](#77-nvidia-nemo-rails--shannon-entropy-filter)
   - [7.8. Trajectory Observability & SWE-agent Windowing](#78-trajectory-observability--swe-agent-windowing)
8. [Testing Hierarchy & Verification Workflow](#8-testing-hierarchy--verification-workflow)
9. [Developer & Agent Command Reference](#9-developer--agent-command-reference)
10. [Dual-Path Synchronization & Chezmoi Tracking](#10-dual-path-synchronization--chezmoi-tracking)

---

## 1. System Mission & The Single Entry Point Mandate

### The Core Problem
Frontier closed-source models (GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro) achieve high benchmark scores through brute compute scaling. However, running autonomous agents locally on consumer hardware (e.g., laptop GPUs with 6GB VRAM) introduces severe failure modes: runaway context windows, tool parameter hallucination, VRAM out-of-memory (OOM) crashes, context rot, and unrecoverable error loops.

### The Hermes Solution
Hermes proves the **Meta-Harness principle**: **Harness engineering beats raw parameter scaling**. By pairing a high-precision, quantized local SLM (Gemma 4 4B Q4_K_M or Qwen 2.5 Coder 3B) with a disciplined, multi-layered agent operating system, Hermes achieves frontier-grade software engineering autonomy on consumer silicon.

### The Single Entry Point Mandate
- **Zero External Wrapper Shell Scripts**: All operations, tools, tests, trajectories, and self-evolution routines must be invocable through the unified Hermes CLI (`hermes <subcommand>` or slash commands like `/agy`, `/ledger`, `/trajectory`).
- **Autonomous Operability**: If an engineer prompts Hermes directly or passes raw tasks to it, Hermes acts as a self-contained operating system capable of inspecting its own logs, proposing code fixes to its own harness, verifying them with zero-regression test gates, and saving clean git snapshots.

---

## 2. Frontier Research Foundations

Hermes is built upon the unified synthesis of research from the world's leading AI laboratories:

| Laboratory | Research Paper / Framework | Core Technique Adopted in Hermes |
| :--- | :--- | :--- |
| **Google DeepMind** | Antigravity 2.0 & ADK 2.8+ | Generative UI artifacts, Markdown alerts, Mermaid charts, Carousels, HTML aux pane, TaskDAG workflows. |
| **Google DeepMind** | Jules Cloud Agent & A2A | Isolated Git worktree sandboxing, `/.well-known/agent-card.json`, JSON-RPC 2.0 streaming. |
| **Google DeepMind** | Gemini 3.8 / 4.0 | Latent cryptographic `thought_signature` preservation across tool execution turns. |
| **Anthropic** | Building Effective Agents & Trinity | Role decomposition: `@architect` (read-only), `@coder` (diff edit), `@tester` (exec), `@critic` (constitutional). |
| **Anthropic** | Claude Code Harness | Surgical `<<<<<<< SEARCH / ======= / >>>>>>> REPLACE` diffs, `SYSTEM_PROMPT_DYNAMIC_BOUNDARY`. |
| **OpenAI** | Agents SDK & Swarm | Type-safe Pydantic v2 handoffs, non-blocking asynchronous delegation loops. |
| **Meta AI & Stanford**| Meta-Harness (arXiv:2603.28052) | Outer-loop self-evolution where the agent inspects harness traces, edits harness Python code, and validates via zero-regression gates. |
| **Meta AI** | EvoHarness-RL | Belief-Progress-Experience (BPE) three-compartment memory workspace (`belief.md`, `progress.md`, `experience.db`). |
| **Microsoft Research**| Magentic-One | Dual Ledgers (Task Ledger for strategic roadmap + Progress Ledger for step tracker) and 2-turn stall circuit breaker. |
| **Microsoft Research**| FrogNano 4B | Zero-distillation RL calibrated to the `[0.3, 0.7]` learnability frontier; filtering tasks that are too easy or noisy. |
| **NVIDIA** | NeMo Guardrails (Colang 2.0) | Input/output execution rails, Shannon Entropy filtering ($1.2 \le H \le 6.5$) to block context bloat and obfuscated payloads. |
| **Hugging Face** | smolagents (CodeAgent) | Code-as-Action: Agent writes executable Python scripts evaluated via AST instead of escaping nested JSON schemas. |
| **Princeton** | SWE-agent | Observation windowing: Truncates tool outputs keeping head/tail 25 lines to prevent context rot. |

---

## 3. Physical Hardware Boundaries & VRAM Invariants

Hermes operates strictly within the physical hardware constraints of an **NVIDIA GeForce RTX 3050 Laptop GPU (6,144 MiB physical VRAM)** under Linux:

```
Total Physical VRAM: 6,144 MiB
┌─────────────────────────────────────────────────────────────┐
│ OS / Wayland / Display Overhead:               ~600 MiB     │
├─────────────────────────────────────────────────────────────┤
│ Active Hermes Ceiling:                        4,800 MiB     │
│  ├─ llama-server Gemma-4 4B Q4_K_M:           ~2,450 MiB    │
│  ├─ Quantized KV Cache (q4_0, 64k tokens):    ~1,024 MiB    │
│  └─ Speculative MTP Draft / Buffer:             ~500 MiB    │
├─────────────────────────────────────────────────────────────┤
│ Safety Headroom / Buffer:                     ~1,344 MiB    │
└─────────────────────────────────────────────────────────────┘
```

### Non-Negotiable Hardware Invariants:
1. **Hard VRAM Cap**: GPU VRAM allocation must **never exceed 4,800 MiB**. Enforced via `nvidia-ml-py` NVML checks.
2. **CPU-Only Neural Retrieval**: Vector embeddings (`fastembed`, BGE-small, Gemma embeddings) **must execute 100% on CPU RAM** via ONNX Runtime. Never allocate CUDA memory for embeddings or AST parsers.
3. **Prefix-Cache Determinism**: Static system prompts (schemas, identity, core rules) are locked at the prefix. Dynamic context is appended strictly at the tail to maintain $>95\%$ KV-cache reuse.
4. **Sandboxed Bash**: Code actions and shell commands execute inside unprivileged Bubblewrap (`bwrap`) or container namespaces with dropped capabilities (`CAP_DROP=ALL`).

---

## 4. The 8 Golden Laws of Hermes OS

Every file edit, code generation, and planning turn must satisfy these 8 laws:

1. **Law 1: Zero Token Waste**  
   Never dump raw, unindexed files into the prompt. Use progressive disclosure: L0 triggers $\to$ L1 summaries $\to$ L2 full source.
2. **Law 2: Spec-First Decomposition**  
   Always formulate structured acceptance contracts before writing or mutating application code.
3. **Law 3: Prefix-Cache Determinism**  
   Separate static system prompt components from dynamic turn state via `SYSTEM_PROMPT_DYNAMIC_BOUNDARY`.
4. **Law 4: Hardware VRAM Guard**  
   Never allow GPU memory to drift past 4,800 MiB. Dense search and tree-sitter indices live on CPU RAM.
5. **Law 5: In-Flight Polyglot Formatting**  
   All file writes are immediately formatted in-memory via Astral Ruff (Python) or Biome (JS/TS/JSON/CSS).
6. **Law 6: 2-Strike Tabu Branch Pruner**  
   If an edit fails 2 consecutive times, halt the branch, revert via git, and mark the failure trajectory as tabu.
7. **Law 7: Quorum Consensus Audit Gate**  
   The Author agent cannot be the Auditor agent. Multi-role checks require consensus ($\ge 0.85$ fitness) before pre-commit.
8. **Law 8: Upstream Engine First**  
   Never invent bespoke framework boilerplate when an upstream standard (Google ADK, NeMo, FastMCP) exists. Use thin calibration adapters to bind them to local hardware.

---

## 5. Codebase Anatomy & Directory Map

```
/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes/
├── AGENTS.md                  # <-- You Are Here: Master Operating Standard & Codex
├── Plan.md                    # Active multi-phase architectural roadmap
├── Summary.md                 # Living engineering certification ledger
├── README.md                  # Project overview, quickstart, and feature matrix
├── Makefile                   # Unified developer entry point (test, exam, sync, server)
├── hermes-pack.yaml           # Declarative pack manifest tracking 26 plugins
├── pyproject.toml             # Python packaging, dependencies, and pytest config
├── .hermes/                   # Core Hermes Agent OS installation directory
│   ├── config.yaml            # Runtime configuration for plugins and gateways
│   ├── SOUL.md                # 176-line cognitive system identity prompt
│   ├── bpe/                   # Belief-Progress-Experience state files (belief.md, progress.md)
│   ├── cache/                 # SQLite WAL databases (trajectories.db, state.db)
│   ├── evolution/             # Spec-kit hypotheses and benchmark baselines
│   ├── memories/              # Long-term semantic and experiential memory stores
│   ├── plugins/               # 26 modular capability plugins (see Roster below)
│   ├── tests/                 # 266-test verification suite (contracts, safety, agent, tools)
│   └── docs/                  # In-depth architectural specifications & C4 diagrams
└── .local_archived/share/chezmoi/ # Chezmoi dotfiles tracking root (git remote)
```

---

## 6. Master Plugin Roster (26 Active Plugins)

Located in `.hermes/plugins/`:

1. **`adk_orchestrator`**: Google ADK 2.8+ TaskDAG orchestration, subagent leasing, and Swarm handoffs.
2. **`agent_os`**: Two-tier agent OS standards, structured plan decomposition, and specification generators.
3. **`agentshield`**: ECC 4-layer defense: semantic intent classification, Shannon secret detection, AST blast radius, and Merkle SHA256 audit ledger.
4. **`antigravity_bridge`**: Google AGY 2.0 Generative UI artifacts, Gemini thought signatures, progressive rule walker, Magentic-One ledgers, and A2A server.
5. **`bpe_workspace`**: Belief-Progress-Experience state workspace preventing task drift across 30+ turns.
6. **`branch_swapper`**: Faraday 27B AI Director two-strike Tabu search branch pruner.
7. **`cactus_uncertainty`**: Hybrid Shannon entropy and uncertainty gating for high-risk actions.
8. **`capability_guard`**: Dynamic role-based tool capability masking and permission isolation.
9. **`cog_verifier`**: Dual-agent cognitive verifier and concept vault.
10. **`context_budget_manager`**: 3-tier hybrid context router (32K HOT / 256K WARM / COLD) with output token budget guards.
11. **`demo_validator`**: Generative UI HTML/CSS/JS validator powered by Biome and ast-grep.
12. **`embedding_gemma`**: CPU-only FastEmbed runtime and CUDA offload prohibition guard.
13. **`gepa_optimizer`**: GEPA-Lite Pareto prompt and skill reflection optimizer.
14. **`mcp_tools`**: FastMCP server, Crawl4AI, ast-grep, Aider search-replace engine, and smolagents code actions.
15. **`nemo_guardrails`**: NVIDIA NeMo Guardrails Colang 2.0 safety policies and execution rails.
16. **`observer_gate`**: 6-point AST observer gate pre-commit hook.
17. **`openskills`**: Anthropic universal skills L0/L1/L2 progressive loader.
18. **`quorum_audit`**: Cross-model quorum consensus gate (Author $\neq$ Auditor).
19. **`recirculation_adapter`**: DeepMind recirculation System-2 prefill reasoning adapter.
20. **`reflective_learner_adapter`**: Episodic learning loop adapter.
21. **`reward_scorer`**: Constitutional reward scorer and FrogNano $[0.3, 0.7]$ learnability frontier filter.
22. **`self_evolution`**: Spec-kit autonomous self-evolution engine and Meta-Harness outer loop.
23. **`skill_intelligence`**: Thought signatures, superpowers registry, dynamic tool retrieval (DTDR), and A2A protocols.
24. **`symbol_index`**: Litho AST codebase memory indexer and C4 architecture diagram generator.
25. **`synergy_bus_adapter`**: Reactive execution and memory synergy bus.
26. **`trajectory_recorder`**: SQLite WAL trajectory recorder with SWE-agent observation windowing.

---

## 7. Subsystems Deep Dive

### 7.1. Antigravity 2.0 (AGY) Bridge & Generative Artifacts
Hermes creates persistent, structured markdown deliverables and generative UI apps inside `<appDataDir>/brain/<conversation-id>/` (or designated project artifact storage):
- **GitHub Alerts**: Use standard blocks:
  ```markdown
  > [!NOTE]
  > Operational background and context.

  > [!IMPORTANT]
  > Non-negotiable hardware and architectural limits.
  ```
- **Mermaid Diagrams**: Visualizes complex workflows with auto-quoted labels:
  ```markdown
  ```mermaid
  flowchart TD
      A["User Prompt"] --> B["NeMo Guardrail"]
      B --> C["BPE Workspace"]
  ```
  ```
- **Multi-Slide Carousels**: 4-backtick carousels with `<!-- slide -->` separators for diff comparisons.
- **HTML Auxiliary Pane**: Generates self-contained single-file HTML applications bundled with KaTeX and Chart.js for live preview in Antigravity Studio.

### 7.2. Cryptographic Thought Signatures
Gemini 3.8 and 4.0 models emit internal reasoning state tokens (`thought_signature`) when requesting function calls.
- **The Protocol Rule**: When Hermes receives a tool call with a `thought_signature`, it registers the token in [`GeminiThoughtSignaturePreserver`](file:///var/home/imshubhamsocial/Projects/Workspace/Personal/hermes/.hermes/plugins/antigravity_bridge/thought_signature.py).
- **The Follow-Up Requirement**: When returning the tool result (`functionResponse`), Hermes re-transmits the unmodified `thought_signature`. Omitting this token causes an immediate `HTTP 400 INVALID_ARGUMENT` rejection from the Gemini backend.

### 7.3. Hierarchical Rules Walker & Progressive Disclosure
Context is resolved according to the Antigravity **"Closer is Better"** hierarchy:
1. **Layer 0 (Global)**: `~/.gemini/antigravity-cli/settings.json` or `~/.agents/`
2. **Layer 1 (Workspace Root)**: `AGENTS.md` / `GEMINI.md`
3. **Layer 2 (Scoped Directory)**: `<subpath>/.agents/rules.md`
- **Progressive Disclosure**: Rules are summarized dynamically: Level 0 (trigger frontmatter) $\to$ Level 1 (summary) $\to$ Level 2 (full text). Injected rule context is strictly bounded to $<400$ tokens.

### 7.4. Magentic-One Dual Ledgers & Stall Circuit Breaker
Long-horizon agent execution often suffers from task drift and cyclical thrashing. Hermes maintains two synchronized ledgers:
- **Task Ledger**: Strategic roadmap, verified ground truths, working hypotheses, and milestone checklists.
- **Progress Ledger**: Step-by-step monitor, sub-agent observations, and stall counter.
- **2-Turn Stall Circuit Breaker**: If 2 consecutive turns yield zero measurable progress, tool dispatch pauses and Hermes initiates a strategic re-planning loop.

### 7.5. Anthropic Trinity & Claude Code Diff Engine
Hermes enforces strict Maker-Verifier isolation:
- **`@architect` (Read-Only)**: Inspects files, greps symbols, formulates specifications. Cannot mutate files or execute bash.
- **`@coder` (Edit-Only)**: Implements changes using Claude Code `<<<<<<< SEARCH / ======= / >>>>>>> REPLACE` surgical diffs. Cannot execute arbitrary shell commands.
- **`@tester` (Exec-Only)**: Runs test suites and captures exit codes inside Bubblewrap (`bwrap`). Cannot modify production application files.
- **`@critic` (Constitutional Reviewer)**: Audits diffs against constitutional principles, Ruff linter rules, and PRM size bounds ($\le 80$ lines).

### 7.6. Meta-Harness Outer Loop & MemRL Self-Evolution
Hermes possesses self-referential improvement capabilities:
- **Outer Loop**: When idle, Hermes inspects execution traces in `trajectories.db`, clusters failure modes, and proposes Python improvements to its own harness tools and prompt templates.
- **Zero-Regression Test Gate**: Every proposed harness mutation must pass the full 266-test contract suite. If a single test fails, the change is instantly rolled back (`git reset --hard`).
- **MemRL Q-Learning**: Updates utility $Q(s, a)$ on experiential memory nodes via runtime Bellman updates in SQLite without neural weight backprop.

### 7.7. NVIDIA NeMo Rails & Shannon Entropy Filter
Every tool input and output passes through Colang 2.0 execution rails:
- **Pre-Execution Rail**: Blocks destructive bash operators (`;`, `&&`, `rm -rf`, `sudo`).
- **Post-Execution Entropy Rail**: Calculates Shannon entropy $H = -\sum p \log_2 p$:
  * $H < 1.2$: Low-entropy repetitive bloat (runaway loops, cyclical text dumps) $\rightarrow$ Blocked.
  * $H > 6.5$: High-entropy anomalies (base64 shellcode, binary exfiltration) $\rightarrow$ Blocked.
  * $1.2 \le H \le 6.5$: Natural language and source code $\rightarrow$ Permitted.

### 7.8. Trajectory Observability & SWE-agent Windowing
All session interactions are recorded into `$HERMES_HOME/cache/trajectories.db` using SQLite in WAL mode:
- **Fields Captured**: `session_id`, `turn_index`, `role`, `prompt`, `reasoning_trace`, `action_code`, `tool_name`, `tool_args`, `tool_output`, `exit_code`, `constitutional_score`.
- **SWE-agent Windowing**: If a command output exceeds 50 lines, Hermes automatically retains the first 25 and last 25 lines, inserting a middle truncation notice to prevent context rot.

---

## 8. Testing Hierarchy & Verification Workflow

The verification suite contains **266 contract tests across 34 test files** with 100% pass rate:

```
.hermes/tests/
├── contracts/        # AGY bridge, thought signatures, ledgers, A2A, entropy rails
├── safety/           # NeMo guardrails, AgentShield security, role enforcer, observer gate
├── agent/            # ADK orchestrator, trajectory recorder, domain fleet, DAG planner
├── tools/            # FastMCP, Aider search-replace diffs, smolagents code actions
└── core/             # Configuration, context budget manager, memory subsystems
```

### Running Tests:
```bash
# Inside ws-hermes distrobox:
cd /var/home/imshubhamsocial/Projects/Workspace/Personal/hermes
.hermes/hermes-agent/venv/bin/pytest .hermes/tests -q
```

---

## 9. Developer & Agent Command Reference

| Command | Purpose |
| :--- | :--- |
| `make test` | Runs the full contract and integration test suite via pytest. |
| `make exam` | Comprehensive system audit: tests, lint, VRAM checks, and doctor. |
| `make doctor` | Validates environment dependencies, binaries, and container runtimes. |
| `make plugins-sync` | Synchronizes all 26 plugins from `hermes-pack.yaml`. |
| `hermes trajectory list` | Lists recent execution sessions and reward scores from `trajectories.db`. |
| `hermes trajectory export`| Exports verified trajectories formatted for SFT/RL fine-tuning. |
| `hermes evolution audit` | Audits failure clusters and triggers Meta-Harness self-evolution. |

---

## 10. Dual-Path Synchronization & Chezmoi Tracking

Hermes maintains dual-path parity between the local project workspace and the host environment:
- **Workspace Project**: `/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes/.hermes/`
- **Host Runtime**: `/var/home/imshubhamsocial/.hermes` (symlinked directly to the project `.hermes/`)
- **Git Version Control**: Tracked via Chezmoi at `/var/home/imshubhamsocial/.local/share/chezmoi` with remote `https://github.com/imshubhamsocial/dotfiles-hermes.git`.

### Synchronizing & Committing Changes:
```bash
# Copy modified files to chezmoi:
cp Plan.md Summary.md Makefile hermes-pack.yaml ~/.local/share/chezmoi/
cp -r .hermes/plugins/* ~/.local/share/chezmoi/private_dot_hermes/plugins/
cp -r .hermes/tests/* ~/.local/share/chezmoi/private_dot_hermes/tests/
cp .hermes/config.yaml ~/.local/share/chezmoi/private_dot_hermes/config.yaml

# Commit and push:
cd ~/.local/share/chezmoi
git add -A
git commit -m "feat: description of change"
git push origin master
```

---

> **Final Invariant for Autonomous Agents**:  
> Always leave the repository cleaner than you found it. Never introduce breaking changes. Never commit without running `pytest`. Maintain the 266+ green test baseline at all times.
