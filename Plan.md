# Hermes Era 9 Master Plan: Frontier-Level AGI Self-Evolving Superintelligence Harness

> **Date**: 2026-09-11  
> **Baseline**: Era 8 complete (220/220 tests passing).  
> **Core Principle**: **Hermes is the single entry point.** Every change, capability, tool registration, and self-evolution step is expressed as native Hermes CLI commands/prompts (`hermes <cmd>`, `hermes learn`, `hermes bpe record`, `hermes evolve`, `hermes note`) and learned via native plugins. No external bash wrappers, no out-of-band hacks.  
> **Hardware Envelope**: NVIDIA RTX 3050 Laptop (6GB VRAM, hard ceiling <= 4,800 MiB). Local inference via `llama-server` with flash-attention and quantized KV-cache. CPU-only embeddings.

---

## Table of Contents
1. [I. Baseline Audit: Issues & Regressions from Era 8](#i-baseline-audit-issues--regressions-from-era-8)
2. [II. Frontier Intelligence Research: Tools, Packages & Repositories Matrix](#ii-frontier-intelligence-research-tools-packages--repositories-matrix)
3. [III. Target Architecture: The AGI-Grade Local Agent Harness](#iii-target-architecture-the-agi-grade-local-agent-harness)
4. [IV. Phased Execution Milestones](#iv-phased-execution-milestones)
   - [Phase 1: Housecleaning & Era 8 Drift Remediation](#phase-1-housecleaning--era-8-drift-remediation)
   - [Phase 2: Comprehensive Trajectory & Session Observability Engine](#phase-2-comprehensive-trajectory--session-observability-engine)
   - [Phase 3: Code-as-Action (smolagents) & ACI Search-Replace Diff Engine](#phase-3-code-as-action-smolagents--aci-search-replace-diff-engine)
   - [Phase 4: Meta-Harness Outer-Loop Autonomous Self-Evolution Engine](#phase-4-meta-harness-outer-loop-autonomous-self-evolution-engine)
   - [Phase 5: Dynamic Tool Dependency Retrieval (DTDR) & Agent2Agent (A2A) Protocols](#phase-5-dynamic-tool-dependency-retrieval-dtdr--agent2agent-a2a-protocols)
   - [Phase 6: Full System Verification, Hardening & Self-Learning Ingestion](#phase-6-full-system-verification-hardening--self-learning-ingestion)
5. [V. Canonical Hermes Single-Entry-Point Execution Commands](#v-canonical-hermes-single-entry-point-execution-commands)
6. [VI. Verification Gates & Success Criteria](#vi-verification-gates--success-criteria)

---

## I. Baseline Audit: Issues & Regressions from Era 8

### 1. Test Suite Baseline
- **Pass Rate**: **220 / 220 tests passing in 10.87s** across 29 test files in `.hermes/tests/`.
- **Zero Failures**: No code breaks or functional test regressions exist in the current codebase.

### 2. Discovered Inconsistencies & Drift to Remediate
1. **`SOUL.md` Location Drift & Content Divergence**:
   - Root `/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes/SOUL.md` is missing (exists only at `.hermes/SOUL.md` with 177 lines).
   - Host `~/.hermes/SOUL.md` is an obsolete 94-line version lacking Section 0 (Rule 0 Mannered Prose Elimination) and modern guardrails.
   - *Remediation*: Synchronize canonical 177-line `SOUL.md` to root and host paths.
2. **Missing C4 Documentation Artifact**:
   - `Summary.md` documented `.hermes/docs/architecture/overview.md`, but it was only emitted to `tmp_path` during unit tests and does not physically exist on disk.
   - *Remediation*: Trigger `CodebaseSymbolIndex` and `C4ArchitectureGenerator` to materialize `.hermes/docs/architecture/overview.md`.
3. **Stale Discarded Skill**:
   - `.hermes/skills/software-development/polars-data-analysis` was marked for deletion in research milestone #18 but remains on disk.
   - *Remediation*: Purge stale directory.
4. **Stale Invariants in `MEMORY.md`**:
   - Line 13 of `.hermes/memories/MEMORY.md` still cites Era 5's "118 contract tests" rather than the current **220 contract tests**.
   - *Remediation*: Update `MEMORY.md` to 220 tests and reflect Era 8/9 invariants.
5. **Empty Session Log Debris**:
   - `.hermes/memories/experiential.jsonl` contains 21 empty session traces (`"title": "Empty Session", "summary": "No messages recorded."`).
   - *Remediation*: Prune empty entries and install guard against zero-turn session commits.
6. **Manifest & Pack Alignment**:
   - `hermes-pack.yaml` only lists 10 plugins, while 24 plugins are active in `.hermes/config.yaml`.
   - 6 plugins (`agent_os`, `cog_verifier`, `observer_gate`, `recirculation_adapter`, `reflective_learner_adapter`, `synergy_bus_adapter`) omit `enabled: true` in their local `plugin.yaml`.
   - `Makefile` hardcodes loops across 9 plugins instead of all 24.
   - *Remediation*: Standardize all 24 `plugin.yaml` manifests and update `hermes-pack.yaml`.

---

## II. Frontier Intelligence Research: Tools, Packages & Repositories Matrix

Exhaustive review of the latest 2025–2026 breakthroughs from Meta AI, OpenAI, Google DeepMind, Microsoft, NVIDIA, and top open-source projects:

| Organization / Project | Key Breakthrough / Tool | Core Architectural Mechanism | Local & Offline (RTX 3050 6GB) Feasibility | Action for Hermes Harness |
|:---|:---|:---|:---:|:---|
| **Meta AI & UIUC** | **EvoHarness-RL** | Demonstrated 8B model matches Claude Opus 4.5 (96.9% vs 96.4%) via structured BPE (Belief-Progress-Experience) memory and cost-aware GRPO. | 100% Local (Low overhead) | **Deepen BPE Workspace** with turn-by-turn state pinning and routine tool annealing. |
| **Stanford IRIS & Meta** | **Meta-Harness** (`meta-harness`, arXiv:2603.28052) | Outer-loop optimization: coding agent inspects its own execution traces, failure logs, and rewrites its own Python harness tools/prompts. SOTA on TerminalBench-2. | 100% Local (Model weights frozen, Python code mutates) | **Implement `hermes harness-evolve`** allowing Hermes to self-diagnose trace failures and patch harness plugins. |
| **Meta Open Source** | **Llama Stack** (`meta-llama/llama-stack`) | Standardized open APIs for local inference, memory, RAG, and tool calling across Ollama, llama.cpp, and vLLM. | 100% Local | Adopt standardized agent checkpoint and tool schemas. |
| **OpenAI** | **OpenAI Agents SDK** (`openai-agents-python`) | Successor to Swarm: lightweight pure-Python agent handoffs (`@architect` -> `@coder` -> `@tester`), eliminating bloated monolithic multi-agent frameworks. | 100% Local (Zero VRAM impact) | **Adopt pure-function Agent Handoffs** to scope tools per role and slash context consumption. |
| **OpenAI** | **Codex Agent / Operator** | Asynchronous background execution in isolated git worktrees with strict ACI tool boundaries. | 100% Local (POSIX worktrees) | **Adopt Worktree Sandboxing** for parallel background speculative attempts. |
| **Google DeepMind** | **Agent Development Kit (ADK 2.0)** | Graph-based workflow DAGs, deterministic task routing, step-level trace inspection. | 100% Local | Keep `adk_orchestrator` as the deterministic pipeline engine. |
| **Google DeepMind** | **Jules & A2A Protocol** | Daemonized background agent loop with machine-to-machine JSON-RPC 2.0 Agent Cards. | 100% Local | Implement A2A agent card interface for multi-subagent capability discovery. |
| **Microsoft Research** | **FrogNano 4B** (Debug-Gym) | 4B coding agent trained purely with RL on synthetic tasks; learnability frontier calibration [0.3, 0.7]. | 100% Local | Calibrate Hermes training curator strictly to the learnability frontier. |
| **Microsoft** | **Microsoft Agent Framework (MAF)** | April 2026 GA: Unification of AutoGen and Semantic Kernel into single enterprise runtime. | 100% Local | Adopt MAF event-driven actor middleware patterns. |
| **Microsoft** | **Magentic-One** | Five-role separation: Orchestrator, WebSurfer, FileSurfer, Coder, Terminal. | 100% Local (Sequential role-shifting) | Enforce sequential role-shifting in a single model context to avoid VRAM exhaustion. |
| **NVIDIA** | **NeMo Guardrails 2026** | Colang 2.0 runtime safety, dynamic tool input/output guardrails, Shannon entropy detection. | 100% Local | Keep `nemo_guardrails` + `agentshield` active as the cognitive-executive boundary. |
| **Hugging Face** | **smolagents** (`huggingface/smolagents`, 29k stars) | **CodeAgents**: Model outputs raw executable Python code rather than escaping nested JSON tool schemas. Eliminates function-calling syntax failures on sub-7B models. | 100% Local (Massive efficiency gain) | **Implement Code-as-Action mode** in Hermes for complex multi-tool bash/file operations. |
| **Aider** | **Aider Pair Programmer** (`Aider-AI/aider`, 49k stars) | ACI (Agent-Computer Interface), Tree-sitter repo map, search/replace unified diffs (`<<<<<<< SEARCH / ======= / >>>>>>> REPLACE`), auto-commit and rollback on test failure. | 100% Local | **Integrate ACI search-replace diff editing** to prevent small models from corrupting whole files. |
| **OpenAutoCoder** | **Agentless** (`OpenAutoCoder/Agentless`) | Phased pipeline (Locate -> Retrieve -> Edit -> Verify) without open-ended ReAct wandering loops. SOTA SWE-bench efficiency. | 100% Local | Standardize task progression into deterministic phases. |
| **Pydantic / JXNL** | **PydanticAI & Instructor** | Type-safe validation and GBNF grammar-constrained decoding over llama.cpp. Guarantees 100% valid JSON and schema conformance. | 100% Local | Enforce GBNF grammar masks on structured tool outputs. |
| **Princeton NLP** | **SWE-agent** (`princeton-nlp/SWE-agent`) | ACI commands: observation head/tail windowing, scroll, targeted grep, preventing context explosion. | 100% Local | Implement observation masking (head 25 + tail 25 lines) on long shell/test outputs. |
| **Langfuse / Phoenix / AgentOps** | **Observability & Trajectory Tracing** | Full session recording, step-level token tracking, time-travel debugging, and offline dataset extraction. | 100% Local (SQLite/DuckDB storage) | **Implement `plugins/trajectory_recorder`** storing rich turns into SQLite for self-learning replay. |

---

## III. Target Architecture: The AGI-Grade Local Agent Harness

```
+---------------------------------------------------------------------------------------+
|                       HERMES RUNTIME: SINGLE CANONICAL ENTRY POINT                     |
|                                (hermes <command> / /slash)                            |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
|                      LAYER 1: COGNITIVE-EXECUTIVE SAFETY BOUNDARY                     |
|  - AgentShield: Shannon Entropy (H > 4.6) + AST Blast Radius + Path Boundary Guard    |
|  - RoleSecurityEnforcer: @architect (read), @coder (edit), @tester (bash/test)        |
|  - NeMo Guardrails: Colang 2.0 destructive command blocklist & loop interception      |
|  - Constitutional Preflight: 8 Golden Laws live pre-execution gating                  |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
|                      LAYER 2: BPE STATE & CONTEXT ORCHESTRATION                      |
|  - Belief State: File tree, git branch, system status, active constraints             |
|  - Progress DAG: Subgoals checklist, completion invariants, failure counts            |
|  - Experience Store: Active reconstruction of prior session errors and fixes         |
|  - 3-Tier Context Router: 32K Hot (GPU KV) / 256K Warm (BM25Plus CPU) / Cold Disk     |
|  - Output Token Budget Guard: Compaction trigger when remaining tokens < 2048         |
|  - Observation Windowing: Head/Tail truncation (max 50 lines) to prevent context rot   |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
|                     LAYER 3: EXECUTION INTERFACE & TOOL SUBSYSTEM                     |
|  - Code-as-Action (smolagents pattern): Model writes Python scripts for multi-step ops|
|  - ACI Search-Replace Diff Engine: Line-anchored <<<<<<< SEARCH / >>>>>>> REPLACE    |
|  - Stateless FastMCP Tool Hub: ast-grep, crawl4ai, duckdb, bubblewrap (bwrap)         |
|  - Dynamic Tool Dependency Retrieval (DTDR): Top 3-5 tools injected on demand         |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
|                 LAYER 4: COMPREHENSIVE TRAJECTORY OBSERVABILITY ENGINE                |
|  - Complete Session Recording: Prompt, thoughts, code action, tool output, test result|
|  - DuckDB / SQLite WAL Storage: Zero cloud egress, microsecond local writes           |
|  - Learnability Frontier Filter: Auto-tag trajectories into [0.3, 0.7] reward band     |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
|                 LAYER 5: META-HARNESS OUTER-LOOP SELF-EVOLUTION ENGINE                |
|  - Autonomous Failure Clustering: Identifies recurring tool/syntax/logic regressions   |
|  - Harness Code Mutator: Self-edits helper scripts, prompts, and tool handlers         |
|  - Spec-Kit Zero-Regression Gate: Mutations committed ONLY if hermes exam = 100%      |
|  - Offline Unsloth QLoRA Coordinator: Low-rank fine-tuning on high-reward buffer      |
+---------------------------------------------------------------------------------------+
```

---

## IV. Phased Execution Milestones

### Phase 1: Housecleaning & Era 8 Drift Remediation
**Objective**: Eliminate file location drift, sync canonical system prompt, prune stale artifacts, and establish 100% parity across project and host paths.
- [ ] **M1.1**: Reconcile and synchronize `SOUL.md`:
  - Verify `.hermes/SOUL.md` (177 lines) has Rule 0 and all 21 rules intact.
  - Copy `.hermes/SOUL.md` to root `/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes/SOUL.md`.
  - Sync `.hermes/SOUL.md` to host `~/.hermes/SOUL.md`.
- [ ] **M1.2**: Generate missing C4 architecture documentation:
  - Run `symbol_index` C4 generator against `.hermes/plugins` to emit `.hermes/docs/architecture/overview.md`.
  - Verify container, context, and component Mermaid diagrams exist on disk.
- [ ] **M1.3**: Purge discarded skills & empty session logs:
  - Delete `.hermes/skills/software-development/polars-data-analysis` and sync to `~/.hermes/skills/`.
  - Sanitize `.hermes/memories/experiential.jsonl` by removing 21 empty session traces.
- [ ] **M1.4**: Update invariants in `MEMORY.md` & manifest parity:
  - Update `.hermes/memories/MEMORY.md` Invariant 4 from 118 to 220 contract tests.
  - Ensure all 24 `plugin.yaml` manifests define `enabled: true`.
  - Update `hermes-pack.yaml` to include all 24 active plugins.
- [ ] **M1.5**: Run `hermes exam` to verify all 220 tests remain pristine green.

### Phase 2: Comprehensive Trajectory & Session Observability Engine
**Objective**: Equip Hermes with full recording of every chat, session, prompt, reasoning trace, tool invocation, environment response, and test outcome into an offline local DuckDB/SQLite store.
- [ ] **M2.1**: Implement `plugins/trajectory_recorder`:
  - `TrajectoryRecorder`: Intercepts `pre_turn`, `post_tool_call`, and `post_turn` lifecycle hooks.
  - Schema: `session_id`, `turn_index`, `role`, `prompt_tokens`, `system_prompt_hash`, `reasoning_trace`, `tool_name`, `tool_args`, `tool_output`, `exit_code`, `test_status`, `constitutional_score`, `timestamp`.
  - Database: `$HERMES_HOME/cache/trajectories.db` (SQLite WAL mode with zero VRAM footprint).
- [ ] **M2.2**: Register native CLI commands:
  - `hermes trajectory list [--limit N]`: Lists recorded agent trajectories.
  - `hermes trajectory show <session_id>`: Displays full turn-by-turn trace with reasoning and tool diffs.
  - `hermes trajectory export [--frontier-only]`: Exports formatted SFT/RL training samples filtered to [0.3, 0.7] reward.
- [ ] **M2.3**: Implement Observation Windowing (SWE-agent / Head-Tail Truncation):
  - In `plugins/agentshield` or `context_budget_manager`, intercept tool stdout/stderr.
  - Truncate outputs > 50 lines to first 25 + `[... N lines truncated ...]` + last 25 lines.
  - Provide `--full` option for explicit inspection.
- [ ] **M2.4**: Contract Tests:
  - Add `test_trajectory_recorder.py` verifying full capture, roundtrip retrieval, and observation truncation.

### Phase 3: Code-as-Action (smolagents) & ACI Search-Replace Diff Engine
**Objective**: Prevent small 4B models from failing due to nested JSON tool escaping or whole-file overwriting by equipping Hermes with code-as-action script execution and Aider-style search/replace diff editing.
- [ ] **M3.1**: Implement ACI Search-Replace Diff Tool in `plugins/mcp_tools` or core tools:
  - `search_replace_block(file_path: str, search_block: str, replace_block: str)`:
    - Finds unique occurrence of `search_block` in `file_path`.
    - Returns deterministic error if `search_block` is ambiguous (matches > 1 locations) or not found.
    - Applies replacement, formats via `ruff` or `ast.parse` syntax validation, and records diff in audit log.
- [ ] **M3.2**: Implement `CodeActionExecutor` (smolagents pattern):
  - Allows Hermes to emit Python scripts inside fenced blocks `python_action` for complex multi-step data or file processing tasks.
  - Executes scripts inside unprivileged `bubblewrap` (`bwrap`) sandbox with access to standard library, `ripgrep`, and project workspace.
  - Intercepts AST syntax errors before execution and feeds line error back to model.
- [ ] **M3.3**: Contract Tests:
  - Add `test_search_replace_diff.py` verifying exact match, multiple-match rejection, syntax check, and git diff emission.
  - Add `test_code_action_executor.py` verifying sandboxed script execution and AST preflight.

### Phase 4: Meta-Harness Outer-Loop Autonomous Self-Evolution Engine
**Objective**: Implement the Meta-Harness (Stanford IRIS / Meta AI) outer-loop self-evolution loop, allowing Hermes to inspect failing execution traces, cluster recurring errors, formulate hypothesis specs, and safely mutate its own harness code.
- [ ] **M4.1**: Implement `plugins/self_evolution/meta_harness.py`:
  - `TraceFailureAnalyzer`: Queries `trajectories.db` for failed turns, clustering failure signatures:
    - `SYNTAX_ERROR`: Malformed code or search/replace mismatches.
    - `VRAM_PRESSURE`: Nearing the 4,800 MiB ceiling.
    - `TOOL_DRIFT`: Excessive repetitive tool calls without progress.
    - `TEST_FAILURE`: Unresolved unit tests.
  - `HarnessProposalEngine`: Formulates targeted code modifications to harness plugins or prompt modules to prevent the identified failure.
  - `SpecVerificationGate`: Executes `hermes exam` in a temporary worktree or transaction before committing modifications. If exam fails, automatically roll back.
- [ ] **M4.2**: Register native CLI command:
  - `hermes harness-evolve [--auto-apply]`: Runs failure analysis across recorded sessions and proposes/applies zero-regression harness improvements.
- [ ] **M4.3**: Contract Tests:
  - Add `test_meta_harness.py` verifying failure clustering, patch formulation, test gate validation, and rollback on regression.

### Phase 5: Dynamic Tool Dependency Retrieval (DTDR) & Agent2Agent (A2A) Protocols
**Objective**: Prevent context prompt bloat by indexing all tools into a local BM25 catalog and dynamically injecting only the top 3–5 tools needed for the active sub-task.
- [ ] **M5.1**: Implement `DynamicToolRetriever` in `plugins/skill_intelligence`:
  - Indexes all tools across active plugins using BM25Plus.
  - Exposes meta-tool `find_tools(task_query: str)` to the agent.
  - Dynamically slots retrieved tool schemas into the active prompt turn, keeping base system prompt < 400 tokens.
- [ ] **M5.2**: Implement Agent2Agent (A2A) Protocol Support:
  - Generate standard JSON-RPC `Agent Cards` for `@architect`, `@coder`, `@tester`, and `@critic` roles.
  - Standardize role handoffs using typed JSON contracts.
- [ ] **M5.3**: Contract Tests:
  - Add `test_dynamic_tool_retrieval.py` verifying tool indexing, semantic keyword matching, and context injection.

### Phase 6: Full System Verification, Hardening & Self-Learning Ingestion
**Objective**: Run complete diagnostic exams, audit trails, blast-radius checks, and ingest learned invariants into BPE workspace and long-term memory.
- [ ] **M6.1**: Run full contract test suite via `hermes exam`:
  - Ensure all existing 220 tests + new Phase 2–5 tests pass with 100% green status.
- [ ] **M6.2**: Run `hermes security-scan` and `hermes audit-trail --verify`:
  - Verify zero credential leaks and 100% cryptographic SHA256 chain integrity.
- [ ] **M6.3**: Internalize Era 9 invariants:
  - Update `belief.md` with Era 9 hardware, observability, and self-evolution invariants.
  - Record progress milestones via `hermes commit-progress`.
  - Ingest key operational lessons via `hermes note`.
- [ ] **M6.4**: Update `Summary.md` with complete implementation report and verification metrics.

---

## V. Canonical Hermes Single-Entry-Point Execution Commands

All phases are driven exclusively through native Hermes commands:

```bash
# ==============================================================================
# Phase 1: Drift Remediation & Parity Sync
# ==============================================================================
hermes doctor
hermes exam

# ==============================================================================
# Phase 2: Trajectory Observability & Recording
# ==============================================================================
hermes trajectory list --limit 10
hermes trajectory show <session_id>
hermes trajectory export --frontier-only

# ==============================================================================
# Phase 3: Code Actions & Search-Replace Diff
# ==============================================================================
hermes tools list --category editing
hermes exam -k "search_replace"

# ==============================================================================
# Phase 4: Meta-Harness Self-Evolution Loop
# ==============================================================================
hermes harness-evolve --dry-run
hermes evolve --verify
hermes exam

# ==============================================================================
# Phase 5: Dynamic Tool Retrieval
# ==============================================================================
hermes superpowers list
hermes exam -k "dynamic_tool"

# ==============================================================================
# Phase 6: System Verification & Memory Ingestion
# ==============================================================================
hermes exam
hermes security-scan
hermes audit-trail --verify
hermes blast-radius --plugin agentshield
hermes track "Era 9 AGI Harness Hardening Complete"
hermes commit-progress
hermes note --category "architecture" "Era 9 Meta-Harness, Trajectory DB, and ACI search-replace diff engine operational."
```

---

## VI. Verification Gates & Success Criteria

1. **Test Gate**: `hermes exam` must pass **>= 235 contract tests** (220 baseline + new Phase 2–5 tests) with 0 failures and 0 regressions in < 15 seconds.
2. **Security Gate**: `hermes security-scan` must report **0 credential leaks** and Shannon entropy compliance ($H <= 4.6$ on generated files).
3. **Cryptographic Integrity Gate**: `hermes audit-trail --verify` must achieve **100% SHA256 hash-chain verification**.
4. **VRAM Ceiling Gate**: Local execution must strictly remain within the **RTX 3050 Laptop <= 4,800 MiB limit**.
5. **Zero-Wrapper Mandate**: 100% of operations must be executed via `hermes <command>` or within the Hermes runtime.
6. **Self-Evolution Gate**: The Meta-Harness engine must be capable of identifying a failing synthetic trajectory, generating a targeted patch, and verifying it against `hermes exam` before commit.
