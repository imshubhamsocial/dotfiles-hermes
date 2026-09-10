# Roadmap 7 — Hermes Codebase De-Bloat, Directory Restructure & Official Tool Migration

> **Generated**: 2026-08-30 · **Scope**: All Python files in `~/.hermes/`
> **Prerequisite**: Domains 1–6 fully implemented and certified (614 contract tests green).

---

## Part 1 — Full Python File Audit

### 1.1 Stray Root-Level Files (Immediate Cleanup Required)

| File | Location | Status | Action |
|------|-----------|--------|--------|
| `compute_latency.py` | Workspace root | ❌ Stray scratch (27 lines, Polars CSV) | **Delete** — one-off experiment |
| `src/__init__.py` | `src/` at workspace root | ❌ Empty (0 bytes) stray placeholder | **Delete** — real package is `.hermes/src/hermes_core/` |
| `src/math_engine.py` | `src/` at workspace root | ❌ Stray 22-line orphan | **Delete** — not imported anywhere |

### 1.2 Stray `build/` Directory (Artifact Pollution)

The workspace-root `build/` and the chezmoi-tracked `build/lib/hermes_core/` are **stale setuptools bdist artifacts** — duplicates of every `hermes_core` module that diverge from source on each reinstall.

**Correct principle**: compiled output lives in `.hermes/.local/lib/python3.13/site-packages/` — NOT in chezmoi source.

```
CURRENT (wrong)                        CORRECT
══════════════════════════════════     ══════════════════════════════════
.local/share/chezmoi/                  .local/share/chezmoi/
├── build/                             ├── private_dot_hermes/
│   └── lib/hermes_core/*.py ← DUP        └── src/hermes_core/*.py  ← SINGLE SOURCE
├── private_dot_hermes/
│   └── src/hermes_core/*.py ← REAL
```

**Fix**:
```bash
cd ~/.local/share/chezmoi
git rm -r --cached build/
echo "build/"        >> .chezmoiignore
echo "*.egg-info/"   >> .chezmoiignore
echo "__pycache__/"  >> .chezmoiignore
git commit -m "chore: stop tracking build artifacts in chezmoi"
```

### 1.3 Complete Python Module Inventory — `hermes_core/` (95 modules)

#### Core Agent Orchestration (Keep, Optimize)
| Module | Purpose | LOC |
|--------|---------|-----|
| `agent.py` | Base Agent/Response/Result types | ~120 |
| `cli.py` | Unified Hermes CLI (U37) | ~850 |
| `runner.py` | HermesRunner SDK (Issue #28) | ~220 |
| `swarm_engine.py` | HermesOrchestrator multi-agent swarm | ~650 |
| `multi_bot_delegation.py` | A2A subagent handoffs | ~180 |
| `domain_fleet.py` | Domain-specialized bot fleet (U67-U71) | ~210 |
| `middleware.py` | FableMiddleware / cognitive governors | ~215 |
| `capability_masks.py` | Role-based tool allow/deny schemas (U3) | ~362 |
| `hook_router.py` | Lifecycle event pub/sub bus (U74) | ~100 |
| `hooks.py` | pre/post_tool_call event hooks (U2) | ~305 |

#### Context & Memory (Keep)
| Module | Purpose | LOC |
|--------|---------|-----|
| `context_compactor.py` | Active context compaction gate (U45) | ~820 |
| `context_sieve.py` | Multi-file AST PageRank sieve (U36) | ~815 |
| `context_window_guard.py` | VRAM-bounded context guard (U65) | ~165 |
| `prompt_slotting.py` | Dual-slot prompt assembly | ~730 |
| `working_memory.py` | WorkingMemoryAnchor + AST gate | ~180 |
| `prefix_cache.py` | KV-cache prefix alignment | ~150 |
| `ring_buffer.py` + `thread_safe_ringbuffer.py` | Circular memory buffers | ~200 |

#### AST / Symbol Intelligence (Keep — No Upstream Replacement)
| Module | Purpose | LOC |
|--------|---------|-----|
| `symbol_graph.py` | Polyglot Tree-Sitter symbol graph (U22) | ~1,240 |
| `knowledge_graph.py` | AST call-graph builder | ~345 |
| `codebase_memory_mcp.py` | MCP symbol knowledge graph (U50) | ~1,314 |
| `lsp_bridge.py` | Live LSP + Tree-Sitter offline bridge (U29) | ~660 |
| `symbol_indexer.py` | Basic symbol indexer | ~230 |
| `ide_substrate.py` | IDE type signature resolver (U20) | ~524 |
| `draft_detective.py` | Adversarial AST fact-checker (U55) | ~315 |

#### Persistence & State (Keep)
| Module | Purpose | LOC |
|--------|---------|-----|
| `database.py` | SQLite WAL connection factory (#06, #07) | ~110 |
| `session_persistence.py` | KV slot save/restore (#33) | ~480 |
| `experience_store.py` | SQLModel episodic memory (#11) | ~215 |
| `flatbuffers_state.py` | FlatBuffers binary checkpoints (#35) | ~95 |
| `opencode_mem.py` | DuckDB + FastEmbed vector memory (U47) | ~709 |
| `cog_vault.py` | Markdown knowledge vault (U49) | ~638 |
| `trajectory.py` | Trajectory stream & hash chain (U6) | ~340 |
| `replay.py` | Deterministic replay runner (U7) | ~255 |

#### Safety & Security (Keep — Enhance with NeMo)
| Module | Purpose | LOC |
|--------|---------|-----|
| `sandbox.py` | Bubblewrap namespace jail (U5) | ~93 |
| `hitl_gateway.py` | HITL risk checkpoint gateway (U27) | ~245 |
| `verification_matrix.py` | Dual-agent consensus gate (U58) | ~116 |
| `cog_verifier.py` | AST + test suite verifier (U49) | ~920 |
| `security_ctf.py` | ELF/CTF security toolsuite (U24) | ~240 |
| `loop_contracts.py` | Turn ceiling & retry contracts | ~157 |

#### Candidate for Official Tool Replacement (Part 3)
| Module | LOC | Replacement Candidate |
|--------|-----|-----------------------|
| `task_graph.py` | ~1,100 | **Google ADK** workflow orchestration |
| `swarm_engine.py` | ~650 | **Google ADK** multi-agent runtime |
| `agent_os.py` | ~610 | **Google ADK** agent lifecycle |
| `agent_os_standards.py` | ~1,550 | **Google ADK** standards (partial) |
| `trajectory.py` | ~340 | **OpenLIT / OpenTelemetry** |
| `replay.py` | ~255 | **OpenLIT** trace replay |
| `web_grounding.py` | ~320 | Keep — migrate `duckduckgo_search` → `ddgs` |
| `fast_research.py` | ~470 | **crawl4ai** or **docling** |
| `google_agentic_substrate.py` | ~860 | **google-adk** natively replaces |

#### Dead / Obsolete (Prune Now)
| Module | Reason | Action |
|--------|--------|--------|
| `executable_extract_code_mode.py` in `hermes_core/` | Duplicate of `bin/` script | **Already deleted in Domain 6** |
| `src/math_engine.py` (workspace root) | Orphan, not imported | **Delete** |
| `compute_latency.py` (workspace root) | One-off Polars scratch | **Delete** |
| `executable_hermes_os_cli.py` in `bin/` | Superseded by `cli.py` HermesCLI | **Retire** |
| `executable_speculative_tool_executor.py` | Overlaps with `test_time_sampler.py` | **Consolidate** |

### 1.4 Bin Scripts Audit (`private_dot_hermes/bin/` — 17 scripts)

| Script | Status |
|--------|--------|
| `executable_cache_ui_assets.py` | Keep |
| `executable_container_cmd.py` | Keep |
| `executable_extract_code_mode.py` | Keep (canonical location) |
| `executable_extract_web_content.py` | Keep |
| `executable_harness_architectural_evolution.py` | Keep (consider ADK migration later) |
| `executable_hermes_os_cli.py` | **Retire** — superseded by HermesCLI |
| `executable_hub_cli.py` | Keep |
| `executable_index_docs.py` | Keep |
| `executable_ingest_document.py` | Keep |
| `executable_observer_gate.py` | Keep |
| `executable_skill_retriever.py` | Keep |
| `executable_skill_router.py` | Keep |
| `executable_speculative_tool_executor.py` | **Consolidate** into `test_time_sampler.py` |
| `executable_verify_harness_integrity.py` | Keep |
| `executable_verify_skills_config.py` | Keep |
| `executable_verify_transcript.py` | Keep |
| `executable_web_grounding.py` | Keep (update import) |

### 1.5 Broken Test Imports Requiring conftest.py Fix

| Test File | Broken Import | Fix |
|-----------|--------------|-----|
| `concurrency_test.py` | `from thread_safe_ringbuffer import ThreadSafeRingBuffer` | `from hermes_core.thread_safe_ringbuffer import ...` |
| `test_arena_graders.py` | `from bin.c01_context_sieve_harness import ...` | Add `bin/` to `sys.path` via conftest.py |
| `test_canary.py` | Same bin import chain | Same fix |
| `test_convergence_queue_relaunch.py` | `from bin import convergence_queue as CQ` | Move `convergence_queue.py` to `hermes_core/` |
| `test_convergence_queue_staleness.py` | Same | Same fix |
| `test_hilo_ab_compare_offline.py` | `from bin import hilo_ab_compare as H` | Move to `hermes_core/` or fix import |

Fix via `tests/conftest.py`:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / ".hermes" / "bin"))
```

---

## Part 2 — Directory Structure Correction Plan

### Target Clean Layout

```
~/.local/share/chezmoi/
├── .chezmoiignore           ← add: build/, *.egg-info/, __pycache__/
├── .chezmoiremove           ← add: deprecated .hermes/bin/executable_hermes_os_cli.py
├── private_dot_hermes/
│   ├── bin/                 ← 15 active executable_ scripts (after retire/consolidate)
│   └── src/hermes_core/     ← 92 modules (SINGLE SOURCE OF TRUTH)
├── tests/
│   ├── harness_contracts/   ← 602 contract tests
│   ├── runners/
│   ├── roadmap6_adversarial/
│   └── conftest.py          ← NEW: sys.path fix
├── roadmap7.md              ← THIS FILE
└── Issues.md / AGENTS.md

~/.hermes/   (git working tree)
├── .gitignore               ← add: /build/, /src/, *.egg-info/
├── pyproject.toml
├── setup.sh
└── tests/ → symlink to chezmoi tests
```

---

## Part 3 — Official Tool Replacement Analysis

### 3.1 Google ADK (`pip install google-adk`)
**Docs**: https://adk.dev | **GitHub**: https://github.com/google/adk-python

Replaces custom orchestration across 4 major modules:

| Custom | LOC | ADK Replacement | Risk |
|--------|-----|-----------------|------|
| `task_graph.py` | ~1,100 | `SequentialAgent`, `ParallelAgent`, `LoopAgent` | 🟡 Medium |
| `swarm_engine.py` | ~650 | `SwarmAgent`, A2A delegation | 🟡 Medium |
| `domain_fleet.py` | ~210 | `Agent(sub_agents=[...])` composition | 🟢 Low |
| `hitl_gateway.py` | ~245 | Built-in HITL tool confirmation | 🟢 Low |
| `multi_bot_delegation.py` | ~180 | `AgentTool`, `transfer_to_agent` | 🟢 Low |
| `google_agentic_substrate.py` | ~860 | ADK natively provides these schemas | 🟢 Low |

**Migration strategy**: Wrap `HermesOrchestrator` as ADK `CustomAgent` first; migrate fleet roles incrementally.

### 3.2 Anthropic FastMCP (`pip install fastmcp`) — Already Integrated
**Already done** in Domain 3. Remaining action:

- Migrate 250 LOC of hand-written `TOOL_SCHEMAS` in `capability_masks.py` to auto-generated schemas via `InstructorSchemaEngine.generate_tool_schema()` — eliminates manual schema maintenance.

### 3.3 NVIDIA NeMo Guardrails (`pip install nemoguardrails`)
**Docs**: https://docs.nvidia.com/nemo/guardrails | **GitHub**: https://github.com/NVIDIA-NeMo/Guardrails

| Custom | LOC | NeMo Replacement | Risk |
|--------|-----|-----------------|------|
| `CRITICAL_COMMAND_PATTERNS` in `hitl_gateway.py` | ~50 | NeMo `input rail` Colang flow | 🟢 Low |
| Role deny logic in `capability_masks.py` | ~100 | NeMo `dialog rail` | 🟡 Medium |
| `loop_contracts.py` ceiling | ~80 | NeMo loop detection + `max_retries` config | 🟢 Low |

**Keep custom**: `cog_verifier.py` AST gate — NeMo has no Tree-Sitter capability.

```python
from nemoguardrails import LLMRails, RailsConfig
config = RailsConfig.from_path("./guardrails_config/")
rails = LLMRails(config)
response = rails.generate(messages=[{"role": "user", "content": user_input}])
```

### 3.4 LangGraph (`pip install langgraph langgraph-swarm`)
**Docs**: https://langchain-ai.github.io/langgraph

| Custom | LOC | LangGraph Replacement | Risk |
|--------|-----|----------------------|------|
| `swarm_engine.py` + `task_graph.py` | ~1,750 | `StateGraph` + `create_swarm()` | 🟡 Medium |
| `branch_swapper.py` — checkpoint rollback | ~400 | `MemorySaver` + checkpoint replay | 🔴 High |
| `replay.py` | ~255 | `BaseCheckpointSaver` replay | 🟢 Low |

**Note**: Google ADK and LangGraph both compete for the same orchestration layer. **Choose one** after evaluation; do not run both.

### 3.5 OpenTelemetry / OpenLIT (`pip install openlit opentelemetry-sdk`)
**Docs**: https://openlit.io

| Custom | LOC | OTel/OpenLIT Replacement | Risk |
|--------|-----|--------------------------|------|
| `trajectory.py` event stream | ~340 | `openlit.init()` auto-instrumentation + custom spans for hash-chain | 🟡 Medium |
| Manual token counting across modules | ~200 | OTel LLM semantic conventions auto-capture | 🟢 Low |
| `replay.py` trajectory read | ~100 | OTel trace export replay | 🟡 Medium |

```python
import openlit
openlit.init(
    otlp_endpoint="http://localhost:4318",
    application_name="hermes-agent-os",
)
```

### 3.6 `ddgs` — Mandatory Package Rename

**Action**: Update `web_grounding.py` and `setup.sh`:
```bash
pip uninstall duckduckgo_search -y && pip install ddgs
```
```python
# web_grounding.py line 175
from ddgs import DDGS  # was: from duckduckgo_search import DDGS
```

### 3.7 `crawl4ai` — Replace Custom HTML Scraper

**Package**: `pip install crawl4ai`

Replaces `fast_research.py` (470 LOC) with async LLM-friendly Markdown extraction. `crawl4ai` provides:
- Async scraping with `AsyncWebCrawler`
- Built-in Markdown conversion
- Token-aware chunking
- LLM-friendly output format

---

## Part 4 — Modules That MUST Remain Custom (No Upstream Replacement)

| Module | Why Irreplaceable |
|--------|------------------|
| `symbol_graph.py` | Hermes-specific polyglot Tree-Sitter graph with custom UNIQUE indexes and `indexed_files` delta caching |
| `cog_verifier.py` + `draft_detective.py` | Domain-specific adversarial AST + claim verification with dual-agent consensus |
| `branch_swapper.py` | Tabu branching with 2-strike rollback — highly domain-specific logic |
| `harness_evolution.py` + `evolution.py` | Custom Pareto genetic evolution over agent execution strategies |
| `session_persistence.py` | llama-server KV-slot persistence + `/slots` save/restore API hooks |
| `test_time_sampler.py` | Local multi-candidate Pareto election tuned for sub-4B SLMs |
| `prefix_cache.py` | llama.cpp-specific prefix KV-cache byte alignment |
| `context_window_guard.py` | RTX 3050/4050 6GB VRAM ceiling enforcement with slot budget math |
| `sandbox.py` | Bubblewrap POSIX namespace jail — OS-level, no Python equivalent |

---

## Part 5 — Priority Action List

### Priority 1 — Immediate (No Capability Risk, < 1 day)

| ID | Action | Effort |
|----|--------|--------|
| D7-01 | Delete `compute_latency.py` from workspace root | ✅ Completed |
| D7-02 | Delete `src/` (stray `__init__.py` + `math_engine.py`) from workspace root | ✅ Completed |
| D7-03 | `git rm -r --cached build/` + add to `.chezmoiignore` | ✅ Completed |
| D7-04 | Add `tests/conftest.py` sys.path fix for broken bin imports | ✅ Completed |
| D7-05 | Migrate `duckduckgo_search` → `ddgs` in `web_grounding.py` + `setup.sh` | ✅ Completed |
| D7-06 | Migrate `TOOL_SCHEMAS` dict in `capability_masks.py` to `InstructorSchemaEngine` | ✅ Completed |
| D7-07 | Consolidate `executable_speculative_tool_executor.py` into `test_time_sampler.py` | ✅ Completed |
| D7-08 | Retire `executable_hermes_os_cli.py` via `.chezmoiremove` | ✅ Completed |

### Priority 2 — Short-Term (Low-Medium Risk, 1-3 days)

| ID | Action | Effort |
|----|--------|--------|
| D7-09 | Replace `fast_research.py` HTML scraper with `crawl4ai` backend | ✅ Completed |
| D7-10 | Integrate OpenLIT for trajectory tracing; wrap `trajectory.py` hash-chain as OTel custom spans | ✅ Completed |
| D7-11 | Add NeMo Guardrails Colang config for input/output rails | ✅ Completed |
| D7-12 | Add `.chezmoiremove` for deprecated files | ✅ Completed |

### Priority 3 — Medium-Term (Architecture-Level, 1-2 weeks)

| ID | Action | Effort |
|----|--------|--------|
| D7-13 | Evaluate Google ADK: wrap `HermesOrchestrator` as ADK `CustomAgent` first | ✅ Completed (`HermesADKCustomAgent` + `docs/evaluations/google_adk_evaluation.md`) |
| D7-14 | Migrate `domain_fleet.py` multi-bot roles to native Google ADK `Agent` composition | ✅ Completed (`build_adk_agent`, `build_adk_fleet`, `build_adk_pipeline` + 5 contract tests green) |
| D7-15 | Evaluate LangGraph vs ADK for `task_graph.py` state machine & `branch_swapper.py` | ✅ Completed (`docs/evaluations/orchestration_selection.md`) |
| D7-16 | Choose ADK vs LangGraph as primary orchestration layer (mutually exclusive) | ✅ Completed (Selected Google ADK; LangGraph rejected to prevent framework redundancy) |

> **Architectural Guardrail**: With D7-13 through D7-16 complete, Google ADK is Hermes's sole primary agent orchestration layer. Law #8 is strictly satisfied: native Google ADK handles agent execution and multi-agent workflows, while thin calibration adapters bind roles to local hardware constraints (port 8138, CPU ONNX, ≤ 4,812 MiB VRAM).

### Priority 4 — Long-Term (Keep Custom)

See Part 4 — no action needed, maintain and extend.

---

## Part 6 — New Packages to Add to `setup.sh`

```bash
#!/usr/bin/env bash
# Domain 7 additions to setup.sh

# Mandatory rename
pip uninstall duckduckgo_search -y
pip install ddgs

# Official Google orchestration substrate
pip install google-adk

# Official NVIDIA safety rails
pip install nemoguardrails

# LangGraph (evaluate vs ADK — choose one)
pip install langgraph langgraph-swarm

# OpenLIT observability (replace custom trajectory logging)
pip install openlit opentelemetry-sdk opentelemetry-exporter-otlp-proto-grpc

# crawl4ai (replace fast_research.py HTML scraper)
pip install crawl4ai
```

---

## Appendix — LOC Reduction Forecast

| Category | Current LOC | Post-D7 LOC | Reduction |
|----------|------------|------------|-----------|
| Orchestration (`task_graph`, `swarm_engine`, `agent_os`, `domain_fleet`) | ~2,570 | ~800 (ADK wrappers) | ~69% |
| Tool schemas (`capability_masks` TOOL_SCHEMAS dict) | ~250 | ~50 (auto-generated) | ~80% |
| Safety rails (`hitl_gateway`, `loop_contracts`) | ~400 | ~100 (NeMo config) | ~75% |
| Trajectory logging (`trajectory`, `replay`) | ~595 | ~150 (OTel wrappers) | ~75% |
| Web scraping (`fast_research`) | ~470 | ~80 (crawl4ai) | ~83% |
| Google substrate (`google_agentic_substrate`) | ~860 | ~0 (ADK native) | ~100% |
| **TOTAL Reducible** | **~5,145** | **~1,180** | **~77%** |
| Irreplaceable custom modules | ~8,000 | ~8,000 | 0% |
| **TOTAL hermes_core** | **~13,145** | **~9,180** | **~30% overall** |

> Non-regression guarantee: All 614 tests must pass green after every migration step before proceeding to the next.
