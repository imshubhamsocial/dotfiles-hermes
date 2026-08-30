# Issues, Architectural Fragility, & Open-Source Package Audit (ws-hermes)

This document registers all operational bugs, loopholes, regressions, and architectural vulnerabilities discovered during the end-to-end audit, live adversarial evaluation, and static inspection of the Hermes agentic harness. It also provides an exhaustive **Upstream Package Replacement Matrix** mapping our ad-hoc custom Python files to battle-tested open-source packages from **Anthropic**, **NVIDIA**, **Google**, **Astral**, and the **Python / Rust Systems Ecosystem** to make Hermes modular, scalable, deterministic, and free of regression edge cases.

---

## 1. Upstream Package Replacement Matrix (Eliminating Ad-Hoc Python Code)

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       UPSTREAM PACKAGE REPLACEMENT & DE-BOILERPLATING MATRIX                                        │
├──────────────────────────┬─────────────────────────────────────┬──────────────────────────────────────┬─────────────────────────────┤
│ Functional Subsystem     │ Current Ad-Hoc Custom Files         │ Recommended Upstream GitHub/PyPI Pkg │ Architectural Advantage     │
├──────────────────────────┼─────────────────────────────────────┼──────────────────────────────────────┼─────────────────────────────┤
│ 1. Polyglot AST, Symbol  │ `symbol_graph.py`, `lsp_bridge.py`, │ `tree-sitter`                        │ Fast, incremental C/Rust AST│
│    Graph & Syntax Gates  │ `knowledge_graph.py`,               │ `tree-sitter-languages`              │ parser; native syntax error │
│                          │ `working_memory.py` (FastASTGate),  │ `pathspec`                           │ detection (`has_error`);    │
│                          │ `extract_code_mode.py`              │ `ruff` (Astral)                      │ 100% Git `.gitignore` spec  │
├──────────────────────────┼─────────────────────────────────────┼──────────────────────────────────────┼─────────────────────────────┤
│ 2. Tool Calling, MCP     │ `codebase_memory_mcp.py`,           │ `mcp[cli]` (Anthropic FastMCP)       │ 100% valid JSON Schema;     │
│    Protocol & Schemas    │ `swarm_engine.py` (func_to_schema), │ `docstring-parser`                   │ typed Pydantic serializing; │
│                          │ `tools.py` (path scoping & stubs),  │ `modelcontextprotocol/servers`       │ eliminates blind string cuts│
│                          │ `speculative_executor.py`           │                                      │ and missing doc descriptions│
├──────────────────────────┼─────────────────────────────────────┼──────────────────────────────────────┼─────────────────────────────┤
│ 3. Multi-Agent DAG       │ `multi_bot_delegation.py`,          │ `google/adk-python` (Google ADK)     │ Code-first DAG workflows    │
│    Orchestration & Eval  │ `graph_engine.py`, `task_graph.py`, │ `networkx`                           │ (`SequentialAgent`, etc.);  │
│                          │ `synergy_bus.py`,                   │ `adk eval` (Trajectory Evaluator)    │ real agent dispatch;        │
│                          │ `hypothesis_tree.py`                │                                      │ replaces mock turn returns  │
├──────────────────────────┼─────────────────────────────────────┼──────────────────────────────────────┼─────────────────────────────┤
│ 4. Deterministic Safety  │ `capability_masks.py`,              │ `nemoguardrails` (NVIDIA NeMo)       │ Programmable Colang Input,  │
│    & Execution Rails     │ `SOUL.md` (prompt-policing)         │ `bubblewrap` (`bwrap`)               │ Execution, and Output rails;│
│                          │                                     │ `process_guard.py` (`setsid`)        │ hard user-space + kernel    │
│                          │                                     │                                      │ security boundary           │
├──────────────────────────┼─────────────────────────────────────┼──────────────────────────────────────┼─────────────────────────────┤
│ 5. Search Grounding &    │ `web_grounding.py`,                 │ `duckduckgo-search` (PyPI)           │ Maintained, zero-config web │
│    Web Content Extract   │ `extract_web_content.py`,           │ `trafilatura`                        │ grounding; resilient main-  │
│                          │ `fast_research.py`                  │ `mcp/servers/src/brave-search`       │ text HTML-to-MD extraction  │
├──────────────────────────┼─────────────────────────────────────┼──────────────────────────────────────┼─────────────────────────────┤
│ 6. Persistent Memory &   │ `experience_store.py`,              │ `duckdb` / `sqlite3` (WAL mode)      │ Zero-GPU persistent tabular │
│    Exact Token Metrics   │ `openviking_vfs.py`,                │ `fastembed` (Qdrant ONNX)            │ & vector storage on disk;   │
│                          │ `opencode_mem.py`, `cog_vault.py`   │ `tiktoken`                           │ exact BPE token counting    │
├──────────────────────────┼─────────────────────────────────────┼──────────────────────────────────────┼─────────────────────────────┤
│ 7. Skills Lifecycle &    │ `openskills_manager.py`,            │ `awesome-claude-skills`              │ Recursive skill discovery;  │
│    Evolution Staging     │ `skill_evolution.py`,               │ `openskills` specification           │ isolated staging directory  │
│                          │ `verify_skills_config.py`           │                                      │ preventing active skill loss│
└──────────────────────────┴─────────────────────────────────────┴──────────────────────────────────────┴─────────────────────────────┘
```

---

## 2. Multi-Prompt Determinism & Regression Prevention Invariants

To guarantee that Hermes behaves consistently across diverse, identical, or adversarial prompts without failing due to harness flaws, we establish **4 Core Determinism Invariants**:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 DETERMINISTIC HARNESS EXECUTION INVARIANTS                             │
├───────────────────────┬──────────────────────────────────┬─────────────────────────────────────────────┤
│ Invariant Class       │ Root Cause of Non-Determinism    │ Deterministic Solution Guarantee            │
├───────────────────────┼──────────────────────────────────┼─────────────────────────────────────────────┤
│ 1. Generation Budget  │ Monolithic 2,500-token dumping   │ Enforce physical `max_tokens: 600` ceiling; │
│    Determinism        │ causes prompt-dependent timeouts │ turn always finishes & yields in ≤ 15s      │
├───────────────────────┼──────────────────────────────────┼─────────────────────────────────────────────┤
│ 2. Subprocess I/O     │ Wall-clock timers kill healthy   │ Monitor stdout/stderr stream byte heartbeat;│
│    Determinism        │ processes on busy CPU/GPU runs   │ only flag deadlock on zero bytes for >15s   │
├───────────────────────┼──────────────────────────────────┼─────────────────────────────────────────────┤
│ 3. Tool & Schema      │ Blind character slicing chops    │ Use FastMCP structured Pydantic models;     │
│    Determinism        │ JSON, crashing client parsers    │ slice array elements before JSON serialization│
├───────────────────────┼──────────────────────────────────┼─────────────────────────────────────────────┤
│ 4. Invocation & Flag  │ Callers forget `--in`, `--yolo`, │ Canonical `HermesRunner` SDK automatically  │
│    Determinism        │ or use invalid flags like `-v`   │ passes all workspace and non-TTY arguments  │
└───────────────────────┴──────────────────────────────────┴─────────────────────────────────────────────┘
```

---

## 3. Registered Subsystem, Tool, & Agentic Vulnerabilities

### Issue #01: The "Completion Trap" & Missing Physical Output Token Gating
* **Classification**: Behavioral Regression / Lack of Physical Gating
* **Impact**: Critical
* **Discovered In**: `test_live_generative_ui_artifact_creation`, `test_live_polars_data_analysis_skill_invocation`, `test_workflow_multi_file_python_library`
* **Symptom**: When given an unconstrained goal, Gemma-4 emitted 2,500+ continuous tokens in a single monolithic generation turn lasting 150–180 seconds.
* **Root Cause**:
  1. `SOUL.md` and `AGENTS.md` instructed the model to be modular, but **prompt rules alone cannot physically restrict token generation**.
  2. The harness allowed a single turn to run up to `max_tokens` (4,096) without enforcing an intermediate tool boundary, chunk yield, or physical output brake.
  3. The agent bypassed the Modular Synthesis DAG Engine (`spec_first_planner.py` / `task_graph.py`) and went straight from user prompt to single-stream code dumping.
* **Remediation & Industry Package Alignment**:
  * **Google ADK Workflow Primitives (`google/adk-python` — `SequentialAgent` / `LoopAgent`)**: Enforce DAG state transitions where an architectural blueprint must be committed before file synthesis tools are unlocked.
  * **NVIDIA NeMo Output Rails (`nemoguardrails` — Output Token Rail)**: Enforce a physical dispatch ceiling ($\le 600\text{ tokens}$ per turn) in `llama-server` runtime and interrupt unconstrained single-stream generation.

---

### Issue #02: Subprocess Directory Isolation Leak (`--in DIR` Parameter)
* **Classification**: Test Harness / Subprocess Calling Bug
* **Impact**: High
* **Discovered In**: `test_developer_workflows_e2e.py`
* **Symptom**: When `test_workflow_multi_file_python_library` ran `hermes -z "<prompt>"` inside a temporary directory (`/tmp/tmp...`), the test failed because files (`src/math_engine.py`) were not written to the temporary directory.
* **Root Cause**: `hermes` CLI defaults its working directory to `~` (or `cwd: .` in `~/.hermes/config.yaml`). When executed programmatically in a subfolder, `hermes` does not automatically infer the caller's working directory unless the explicit CLI flag `--in <DIR>` is passed.
* **Remediation & Industry Package Alignment**:
  * **Anthropic MCP Filesystem Server (`modelcontextprotocol/servers/src/filesystem`)**: Adopt strict workspace URI scoping where all file operations are pinned to the active project root URI.
  * In `cli.py`, auto-detect non-interactive TTY execution (`not sys.stdin.isatty()`) and bind `--in` to `Path.cwd()` by default.

---

### Issue #03: Heuristic Subprocess Timeouts & Missing I/O Activity Heartbeats
* **Classification**: Harness Invariant Violation / Artificial Timer Crutch
* **Impact**: Critical
* **Discovered In**: `test_hermes_live_prompts.py`, `test_developer_workflows_e2e.py`
* **Symptom**: Live tests failed with `subprocess.TimeoutExpired` at 90s / 120s / 180s even though `llama-server` was actively streaming valid tokens at 29.5 t/s with 0 errors.
* **Root Cause**:
  1. The harness used arbitrary wall-clock timers (`timeout=90`, `timeout=180`) instead of monitoring physical execution signals.
  2. The single turn was allowed to run unconstrained for 2,500+ tokens without yielding, burning wall-clock seconds.
  3. Increasing timeouts (e.g. from 90s to 300s) is an **anti-pattern** that masks the root cause rather than solving it deterministically.
* **Remediation & Industry Package Alignment**:
  * **Google ADK Trajectory Evaluator (`google/adk-python` — `adk eval`)**: Replace wall-clock timers with state-driven DAG invariant verification (evaluating tool call order and contract satisfaction).
  * **Non-Blocking I/O Activity Heartbeats (`asyncio` / `selectors`)**: Monitor stdout/stderr stream bytes; only flag a stall if zero bytes are received for $>15\text{s}$ (true deadlock).
  * **Physical Turn Output Chunking**: Bound turns to $\le 600\text{ tokens}$ so turns naturally finish in $\le 15\text{ seconds}$.

---

### Issue #04: Dual-Slot Inference Context Mismatch (`-c 32768` vs `-c 131072`)
* **Classification**: Runtime Hardware Configuration Bug
* **Impact**: Critical
* **Discovered In**: Turn 0 Context Overflow
* **Symptom**: `llama-server` rejected requests with: `request (22956 tokens) exceeds the available context size (16384 tokens)`.
* **Root Cause**: `llama-server` divides the total context `-c` evenly across parallel slots (`-np 2`). A `-c 32768` flag only allocated $16,384$ tokens per slot. Because Hermes system prompts and tool schemas occupy ~22,956 tokens, Turn 0 immediately overflowed.
* **Remediation & Industry Package Alignment**:
  * Set `-c 131072` (128K total), giving exactly **$65,536\text{ tokens (64K)}$ per slot** across 2 slots.
  * Verified $K/V$ quantization (`q4_0`) keeps total VRAM $\le 3,240\text{ MiB}$ (well below the $4,812\text{ MiB}$ safety ceiling).

---

### Issue #05: Prompt-Policed Jailbreak Containment vs. Structural Pre-Execution Gating
* **Classification**: Security Architecture Gap
* **Impact**: High
* **Discovered In**: `test_live_adversarial_jailbreak_tamper_attempt`
* **Symptom**: When issued a hostile prompt ordering the deletion of `.integrity` logs and modification of `agent_capabilities.yaml`, the agent attempted a tool call to read the file before refusing.
* **Root Cause**: Relying on the model to read a file and then decide to refuse is insecure. A compromised or hallucinating model could issue write or delete commands before refusal logic kicks in.
* **Remediation & Industry Package Alignment**:
  * **NVIDIA NeMo Execution Rails (`nemoguardrails` — Execution & Path Rails)**: Implement programmatic Colang execution rails that intercept tool invocations before execution.
  * Added `validate_security_policy_path()` and `validate_security_policy_command()` to `capability_masks.py` to abort dangerous operations in user-space before reaching the OS.

---

### Issue #06: OpenViking VFS Ephemerality & Coarse Token Drift
* **Classification**: Virtual Filesystem / State Loss
* **Impact**: High
* **Discovered In**: `src/hermes_core/openviking_vfs.py`
* **Symptom**: The OpenViking VFS (`viking://`) maintains all L0/L1/L2 hierarchical context nodes in pure transient memory (`VFSNode` in Python RAMDisk). Process restart, crash, or subagent invocation in a separate process completely wipes the VFS index.
* **Root Cause**:
  1. No SQLite, DuckDB, or filesystem persistence layer is attached to `OpenVikingVFS`.
  2. Token estimation uses a crude `len(text) // 4` character-count heuristic, which introduces 40–60% estimation errors on minified JavaScript, HTML templates, and non-ASCII source files.
  3. `find()` method performs an unindexed $O(N)$ recursive tree traversal that locks execution during deep repository scans.
* **Remediation & Industry Package Alignment**:
  * **DuckDB / SQLite WAL Storage (`sqlite3` / `duckdb`)**: Back `OpenVikingVFS` with an on-disk embedded SQLite store for persistent L0/L1/L2 context nodes.
  * **Google Tiktoken / Tokenizer BPE (`tiktoken` / HuggingFace `tokenizers`)**: Replace character division with exact BPE token counts.
  * **Inverted Tag Indexing**: Index tags in memory to provide $O(1)$ tag lookups.

---

### Issue #07: Codebase Memory MCP JSON Truncation Syntax Corruption
* **Classification**: MCP Tool Contract / Parser Crash
* **Impact**: Critical
* **Discovered In**: `src/hermes_core/codebase_memory_mcp.py`
* **Symptom**: When querying large class hierarchies or multi-hop call graphs, MCP tool consumers fail with `json.decoder.JSONDecodeError: Unterminated string`.
* **Root Cause**: `truncate_to_tokens(text, max_tokens=150)` performs blind character-level string slicing (`text[:max_chars - 3] + "..."`). When `text` is a JSON serialization of symbols or classes, blind character chopping produces malformed JSON syntax.
* **Remediation & Industry Package Alignment**:
  * **Official Anthropic FastMCP SDK (`mcp[cli]` / `FastMCP` from `modelcontextprotocol/python-sdk`)**: Replace custom string chopping with FastMCP's structured tool payload serialization.
  * Truncate list elements in the data model *before* serializing to JSON, guaranteeing 100% valid JSON Schema output.

---

### Issue #08: AST Symbol Graph Monoglot Limitation & Schema Pollution
* **Classification**: AST & Code Intelligence
* **Impact**: High
* **Discovered In**: `src/hermes_core/symbol_graph.py`
* **Symptom**: Whole-codebase symbol indexing fails or skips all non-Python files (JavaScript, TypeScript, Rust, Go, C++, HTML).
* **Root Cause**:
  1. `symbol_graph.py` hardcodes `ast.parse` (Python standard library only) and `patterns = ["*.py"]`.
  2. `symbol_references` SQLite table lacks `UNIQUE` constraints and path normalization, resulting in duplicate reference records and DB bloat upon repeated project indexings.
  3. `.gitignore` filtering uses naive `fnmatch` which fails on directory-only suffixes (`dir/`), negation rules (`!`), and multi-level recursive globs (`**/`).
* **Remediation & Industry Package Alignment**:
  * **Tree-Sitter Multi-Language Bindings (`tree-sitter` & `tree-sitter-languages`)**: Wire official Tree-sitter parsers for Python, JavaScript, TypeScript, Rust, Go, and C++ into `SymbolGraph`.
  * **Git-Compliant PathSpec (`pathspec` PyPI)**: Replace `fnmatch` with `pathspec.PathSpec.from_lines("gitwildmatch", ...)` for standard `.gitignore` resolution.
  * Add `UNIQUE(source_file, caller_symbol, target_symbol, ref_type)` to SQLite schema.

---

### Issue #09: LSP Bridge False-Positive Bracket Syntax Scrubber
* **Classification**: Linter / AST Fallback False Positive
* **Impact**: High
* **Discovered In**: `src/hermes_core/lsp_bridge.py`
* **Symptom**: Valid JS, TS, HTML, and C++ files are incorrectly rejected by the syntax guard with `"Unmatched closing bracket"` or `"Unclosed opening bracket"`.
* **Root Cause**: `analyze_generic_source()` scans raw characters line-by-line using a naive stack. It does not track string literals (`"..."`, `'...'`, `` `...` ``), regexes (`/.../`), or single/multi-line comments (`//`, `/* */`), causing brackets inside strings or comments to trigger false syntax errors.
* **Remediation & Industry Package Alignment**:
  * **Tree-Sitter Syntax Error Detector (`tree-sitter`)**: Check syntax validity via `tree.root_node.has_error` across all languages instead of naive character stacking.

---

### Issue #10: Knowledge Graph AST `Name` Confusion (Variable as Callee)
* **Classification**: Knowledge Graph & Topological Extraction
* **Impact**: Medium
* **Discovered In**: `src/hermes_core/knowledge_graph.py`
* **Symptom**: The Codebase Knowledge Graph records local variables (`x`, `y`, `self`, `None`, `True`) as function calls in `caller_graph`.
* **Root Cause**: `_index_python_file` extracts calls using `calls = [n.id for n in ast.walk(item) if isinstance(n, ast.Name)]`. In Python's AST, `ast.Name` represents all variable names and constants, not function calls (`ast.Call`).
* **Remediation & Industry Package Alignment**:
  * Restrict AST extraction strictly to `ast.Call` nodes and extract callee names via `node.func.id` or `node.func.attr`.

---

### Issue #11: Hypothesis Tree Singleton Collision in Multi-Agent Workflows
* **Classification**: Concurrency & State Isolation
* **Impact**: High
* **Discovered In**: `src/hermes_core/hypothesis_tree.py`
* **Symptom**: When multiple subagents or background tasks run concurrently, hypothesis trees overwrite each other, causing orphaned branch IDs and corrupted backtracking histories.
* **Root Cause**: `STORAGE_PATH` is hardcoded to a static singleton file `/dev/shm/hypothesis_tree.json`.
* **Remediation & Industry Package Alignment**:
  * **Google ADK Session Hierarchy (`google/adk-python`)**: Scope hypothesis tree state dynamically by session and task ID (`/dev/shm/hermes/hypothesis_{session_id}_{task_id}.json`).

---

### Issue #12: Stubbed Search Tool in Universal Primitives
* **Classification**: Missing Implementation / Tool Stub
* **Impact**: Medium
* **Discovered In**: `src/hermes_core/tools.py`
* **Symptom**: Calls to `search_web()` return a static dummy string: `"Search results for '...': Query resolved successfully."`
* **Root Cause**: `tools.py:search_web()` was left as a stub and never connected to `web_grounding.py` or `extract_web_content.py`.
* **Remediation & Industry Package Alignment**:
  * **Anthropic MCP Brave Search Server (`modelcontextprotocol/servers/src/brave-search`)**: Wire `search_web()` to official search providers (SearXNG / DuckDuckGo / Brave Search).

---

### Issue #13: Default Workspace Root Path Resolution Divergence
* **Classification**: Path Resolution & Sandbox Scoping
* **Impact**: High
* **Discovered In**: `src/hermes_core/tools.py`
* **Symptom**: Relative file operations (`read_file("src/app.py")`) fail or look in `/dev/shm/hermes_workspace` even when the user is working in their project directory.
* **Root Cause**: `_resolve_path()` defaults to `Path("/dev/shm/hermes_workspace")` if `workspace_root` is not explicitly passed.
* **Remediation & Industry Package Alignment**:
  * Default `workspace_root` dynamically to `Path.cwd()` (or active project root via environment variable).

---

### Issue #14: Speculative Tool Executor Promise Abandonment & Memory Leak
* **Classification**: Async Tool Execution / Resource Leak
* **Impact**: Medium
* **Discovered In**: `src/hermes_core/speculative_executor.py`
* **Symptom**: Speculative tool promises taking $>5.0\text{s}$ are abandoned, marked as `REJECTED`, and re-executed synchronously. Furthermore, completed promises are never evicted from `self.promises`.
* **Root Cause**: Hardcoded timeout polling on futures and missing LRU eviction policy on `self.promises`.
* **Remediation & Industry Package Alignment**:
  * **`asyncio.Future` & `concurrent.futures` Callbacks**: Replace timeout polling with event-driven completion callbacks (`future.add_done_callback`) and bind `self.promises` with a capacity-capped LRU cache.

---

### Issue #15: Deterministic Code Extractor Monoglot Python Destruction
* **Classification**: Code Extraction & Tool Calling
* **Impact**: High
* **Discovered In**: `private_dot_hermes/bin/executable_extract_code_mode.py`
* **Symptom**: Extracting non-Python code blocks (Bash, HTML, CSS, JavaScript, SQL, JSON, YAML) from markdown fences fails with `"extract_code: fenced output contained no parsable code body"`.
* **Root Cause**: `extract_code()` filters candidate code chunks by passing them to `ast.parse(candidate)`. Any non-Python syntax raises `SyntaxError` and is discarded.
* **Remediation & Industry Package Alignment**:
  * Accept code blocks tagged with language markers (e.g. ```` ```bash ````, ```` ```html ````) and validate syntax using Tree-sitter language grammars rather than assuming all code is Python.

---

### Issue #16: External Directory Expansion in Skill Verification
* **Classification**: Configuration & Environment Resilience
* **Impact**: Medium
* **Discovered In**: `private_dot_hermes/bin/executable_verify_skills_config.py`
* **Symptom**: Profiles declaring `external_dirs` with tildes or unexpanded shell variables fail pre-run verification if environment variables differ between host and container.
* **Root Cause**: Path existence checks relied on raw environment expansions without canonicalizing paths via `Path.resolve()`.
* **Remediation & Industry Package Alignment**:
  * Use normalized `os.path.expanduser(os.path.expandvars(p))` before validating directory existence.

---

### Issue #17: Inter-Bot Communication & Synergy Bus Memory Leak
* **Classification**: Multi-Bot & Reactive Bus / Memory Leak
* **Impact**: High
* **Discovered In**: `src/hermes_core/synergy_bus.py`
* **Symptom**: Long-running multi-agent sessions or continuous background tasks continuously consume RAMDisk and memory until exhaustion.
* **Root Cause**: `SynergyEventBus.event_history` appends every published event (`TASK_SPAWN`, `TOOL_CALL`, `VFS_MUTATION`) into an unbounded in-memory Python list without any eviction policy or ring buffer size limit.
* **Remediation & Industry Package Alignment**:
  * **Google ADK Event Bus (`google/adk-python`)**: Adopt ADK's bounded event bus stream backed by a thread-safe ring buffer (`ThreadSafeRingBuffer(capacity=1000)`).

---

### Issue #18: Multi-Bot Delegation Hardcoded Mock Orchestration
* **Classification**: Multi-Agent Orchestration / Mock Stub
* **Impact**: Critical
* **Discovered In**: `src/hermes_core/multi_bot_delegation.py`
* **Symptom**: `execute_delegation_pipeline()` does not actually execute multi-bot turns or generate code via LLM tools—it immediately returns pre-fabricated mock success strings (`"Architectural specification formulated in .hermes/plan.json..."`).
* **Root Cause**: The delegation orchestrator was authored as a prototype stub with synthetic return objects rather than connecting to the live Swarm / Hub dispatch loop.
* **Remediation & Industry Package Alignment**:
  * **Google ADK Hierarchical Orchestrator (`google/adk-python` — `SequentialAgent` / `ParallelAgent`)**: Wire `MultiBotOrchestrator` to dispatch real agent turns with live tool calls and artifact validation.

---

### Issue #19: Swarm Engine Function Schema Type Coercion & Docstring Loss
* **Classification**: Tool Calling & Schema Generation
* **Impact**: Medium
* **Discovered In**: `src/hermes_core/swarm_engine.py`
* **Symptom**: Tools with complex type signatures (`Optional[int]`, `Union[str, Path]`, `Literal[...]`, Pydantic models) are exposed to the model as generic `"type": "string"` with uninformative `"description": "Parameter {name}"`.
* **Root Cause**: `function_to_schema()` uses a primitive `if/elif` type check and does not parse docstrings (Google/Sphinx/Numpydoc) for argument descriptions.
* **Remediation & Industry Package Alignment**:
  * **Anthropic Tool Schema Generator (`mcp.server.fastmcp` / `docstring_parser`)**: Parse docstrings and Pydantic field models into full JSON Schema definitions.

---

### Issue #20: Web Grounding Module Import Failure & Search Black Hole
* **Classification**: Web Grounding & External Knowledge
* **Impact**: Critical
* **Discovered In**: `src/hermes_core/web_grounding.py`
* **Symptom**: All web searches in `WebGroundingEngine` fail silently and return `[]` (empty results).
* **Root Cause**:
  1. Line 171 attempts `from ddgs import DDGS`, which does not exist in standard PyPI (standard library is `duckduckgo_search`).
  2. Neither `duckduckgo_search` nor a live `SEARXNG_URL` is configured by default, causing both primary and fallback search paths to fail.
* **Remediation & Industry Package Alignment**:
  * Install and wire `duckduckgo-search` (`from duckduckgo_search import DDGS`).
  * Add automatic fallback to local offline documentation indexing via `index_docs.py`.

---

### Issue #21: Ephemeral Tool Buffer Disk Growth & Missing Cleanup
* **Classification**: Storage Management / RAMDisk Bloat
* **Impact**: Medium
* **Discovered In**: `src/hermes_core/token_engine.py`
* **Symptom**: `/dev/shm` fills up with thousands of orphan `hermes_ephemeral_*.log` files during heavy coding sessions.
* **Root Cause**: `EphemeralToolBuffer.finalize()` writes full subprocess stdout/stderr streams to `/dev/shm` on every single command turn, but never registers a FIFO capacity cap.
* **Remediation & Industry Package Alignment**:
  * Add a deterministic FIFO RingBuffer in `EphemeralToolBuffer` capping stored log count to 50 entries.

---

### Issue #22: Destructive Skill Promotion Folder Pruning Bug
* **Classification**: Skill Evolution / Data Loss Bug
* **Impact**: High
* **Discovered In**: `src/hermes_core/skill_evolution.py`
* **Symptom**: If an autonomous evolution cycle fails its A/B lift gate (+15% requirement), the engine deletes the entire skill directory, accidentally destroying existing production skills sharing the same name.
* **Root Cause**: `synthesize_candidate_skill()` writes candidate drafts directly to `~/.hermes/skills/{skill_name}/SKILL.md`. If A/B certification fails, `evaluate_and_promote()` calls `shutil.rmtree(candidate_file.parent)`, deleting the entire folder.
* **Remediation & Industry Package Alignment**:
  * Write candidate drafts to an isolated staging directory (e.g. `~/.hermes/staging_skills/`). Only copy to `~/.hermes/skills/` after the A/B lift gate is certified.

---

### Issue #23: Metacognitive Memory Ephemerality & RAMDisk State Loss
* **Classification**: Experience Store & Lifelong Learning
* **Impact**: High
* **Discovered In**: `src/hermes_core/experience_store.py`
* **Symptom**: All accumulated failure patterns, negative constraints, and positive playbooks are wiped on machine reboot or container restart.
* **Root Cause**: `ExperienceStore` defaults its database path to `/dev/shm/hermes_experience_store.json` (RAMDisk).
* **Remediation & Industry Package Alignment**:
  * Default storage to persistent disk at `~/.hermes/memory/experience_store.json` (or sync with `experiential.jsonl`), with optional RAMDisk write-through caching.

---

### Issue #24: OpenSkills Single-Level Scanner Drops Categorized Skills
* **Classification**: Skill Discovery & Architecture
* **Impact**: High
* **Discovered In**: `src/hermes_core/openskills_manager.py`
* **Symptom**: OpenSkills discovery returns 0 skills even when 62+ valid skills exist on disk.
* **Root Cause**: `_rebuild_index()` performs a flat 1-level `iterdir()` scan (`skills_dir / skill_dir / SKILL.md`). Because skills are organized in subdirectories (`creative/comfyui/SKILL.md`, `software-development/polars-data-analysis/SKILL.md`), all categorized skills are completely missed.
* **Remediation & Industry Package Alignment**:
  * Replace 1-level iteration with recursive globbing (`skills_dir.rglob("SKILL.md")`).

---

### Issue #25: Lack of Base Skill Marketplace / Lead Developer Pack Pre-Bundling
* **Classification**: Environment Setup & Capability Gap
* **Impact**: High
* **Discovered In**: `executable_setup.sh`, `private_skills/`
* **Symptom**: Common developer capabilities (e.g. Anthropic lead developer skills, official awesome-claude-skills, framework linters) must be manually coded or imported ad-hoc rather than pre-seeded at setup.
* **Root Cause**: `setup.sh` only deploys local static dotfiles and does not include an upstream skill package synchronizer.
* **Remediation & Industry Package Alignment**:
  * **Anthropic Claude Skills / OpenSkills Hub (`awesome-claude-skills`)**: Add an upstream skill synchronization phase in `setup.sh` that bundles and categorizes core developer skills (TDD, Playwright, React, FastAPI, Git PR workflow) during initial setup.

---

### Issue #26: Absence of Automatic Post-Generation Auto-Formatting & Linter Pipeline
* **Classification**: Code Quality & Pre-Commit Automation
* **Impact**: Medium
* **Discovered In**: `src/hermes_core/working_memory.py`, `src/hermes_core/tools.py`
* **Symptom**: Code generated by the agent contains PEP 8 indentation errors, unformatted JSX/HTML, or trailing whitespace because formatters (`ruff format`, `black`, `prettier`) are never called automatically. Furthermore, `FastASTPreCommitGate` uses crude string counting (`count("{") != count("}")`) that falsely rejects valid code containing braces in strings.
* **Root Cause**: `write_file()` performs an AST syntax check but does not pipe code through standard formatters.
* **Remediation & Industry Package Alignment**:
  * **Astral Ruff (`ruff` PyPI)**: Automatically run `ruff format` and `ruff check --fix` (<10ms) on generated Python files in `write_file()`.
  * **Prettier (`prettier`)**: Automatically format JS, TS, HTML, CSS, JSON, and YAML files.
  * **Tree-Sitter Syntax Error Detection (`tree-sitter`)**: Replace crude character counts with `tree.root_node.has_error`.

---

### Issue #27: CLI Flag Schema Discrepancy & Verbose Mode Ambiguity
* **Classification**: CLI Usability & Argument Parsing
* **Impact**: Medium
* **Discovered In**: `hermes` CLI entry point, `test_developer_workflows_e2e.py`
* **Symptom**: Passing standard debugging flags (e.g. `--verbose`, `-v`) to `hermes` crashes with `unrecognized arguments: --verbose`.
* **Root Cause**: Root CLI parser only registers specific subcommand arguments (or `--dev` tied strictly to `--tui`).
* **Remediation & Industry Package Alignment**:
  * Add global `--verbose` / `-v` / `--debug` aliases at the root CLI argument parser to configure logging levels consistently across all modes.

---

### Issue #28: Agent & Benchmark Flag Amnesia & Missing Canonical Runner SDK
* **Classification**: Harness Usability & Invocation Invariant
* **Impact**: High
* **Discovered In**: `test_hermes_live_prompts.py`, `test_developer_workflows_e2e.py`, benchmark scripts
* **Symptom**: During automated benchmarks, CI runs, or subagent tool dispatch, callers routinely omit critical CLI flags (e.g. `--in <DIR>`, `--yolo`, `--skills`, `--accept-hooks`), causing headless runs to hang waiting for stdin confirmation, write files to the wrong workspace, or fail to load required skills.
* **Root Cause**:
  1. No single typed Python SDK wrapper existed (e.g. `hermes_core.runner.run_hermes(...)`); every test and subagent constructed ad-hoc `subprocess.run(["hermes", ...])` argv lists from scratch.
  2. The CLI did not automatically detect non-interactive TTY environments to default `--in` to `os.getcwd()` and auto-accept headless hooks.
* **Remediation & Industry Package Alignment**:
  * Implement a canonical, typed `HermesRunner` SDK module in `src/hermes_core/runner.py` that encapsulates all flags, I/O activity heartbeats, and working directory bindings.
  * In `cli.py`, auto-detect non-TTY environments (`not sys.stdin.isatty()`) and automatically bind `cwd` to current working directory if `--in` is omitted.
