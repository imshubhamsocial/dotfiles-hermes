# Issues & Architectural Fragility Audit (ws-hermes)

This document registers all operational bugs, loopholes, regressions, and architectural vulnerabilities discovered during the end-to-end audit, live adversarial evaluation, and static codebase inspection of the Hermes agentic harness. It also provides an exhaustive physical audit of where the codebase relies on artificial timeouts, arbitrary token budgets, fixed context limits, hardcoded sleeps, and prompt-policed constraints rather than deterministic physical mechanisms.

---

## 1. Registered Adversarial & Architecture Findings

### Issue #01: The "Completion Trap" & Missing Physical Output Token Gating
* **Classification**: Behavioral Regression / Lack of Physical Gating
* **Impact**: Critical
* **Discovered In**: `test_live_generative_ui_artifact_creation`, `test_live_polars_data_analysis_skill_invocation`, `test_workflow_multi_file_python_library`
* **Symptom**: When given an unconstrained goal (e.g. *"Generate a complete standalone HTML dashboard with inline CSS and JS"*), Gemma-4 emitted 2,500+ continuous tokens in a single monolithic generation turn lasting 150–180 seconds.
* **Root Cause**:
  1. `SOUL.md` and `AGENTS.md` instructed the model to be modular and concise, but **prompt rules alone cannot physically restrict token generation**.
  2. The harness allowed a single turn to run up to `max_tokens` (4,096) without enforcing an intermediate tool boundary, chunk yield, or physical output brake.
  3. The agent bypassed the Modular Synthesis DAG Engine (`spec_first_planner.py` / `task_graph.py`) and went straight from user prompt to single-stream code dumping.
* **Remediation**:
  * Implement a physical output token ceiling ($\le 600 - 800\text{ tokens}$ per turn) at the engine dispatch level.
  * Enforce schema-level DAG requirements: the agent must emit an architectural skeleton or task graph before receiving access to full file synthesis tools.
  * Integrate the 6-point Observer Gate between file chunks (HTML skeleton $\rightarrow$ CSS styles $\rightarrow$ JS logic $\rightarrow$ validation).

---

### Issue #02: Subprocess Directory Isolation Leak (`--in DIR` Parameter)
* **Classification**: Test Harness / Subprocess Calling Bug
* **Impact**: High
* **Discovered In**: `test_developer_workflows_e2e.py`
* **Symptom**: When `test_workflow_multi_file_python_library` ran `hermes -z "<prompt>"` inside a temporary directory (`/tmp/tmp...`), the test failed because files (`src/math_engine.py`) were not written to the temporary directory.
* **Root Cause**: `hermes` CLI defaults its working directory to `~` (or `cwd: .` in `~/.hermes/config.yaml`). When executed programmatically in a subfolder, `hermes` does not automatically infer the caller's working directory unless the explicit CLI flag `--in <DIR>` is passed.
* **Remediation**:
  * Updated test runner helper to always append `["--in", str(cwd)]` whenever a custom working directory is provided.
  * Ensure programmatic SDK wrappers explicitly propagate `in_dir` to the runtime environment.

---

### Issue #03: Fragile Subprocess Timeouts in Live Test Harnesses
* **Classification**: Test Harness Invariant Violation
* **Impact**: Medium
* **Discovered In**: `test_hermes_live_prompts.py`
* **Symptom**: 3 live tests failed with `subprocess.TimeoutExpired` at 90s / 120s even though `llama-server` was actively generating valid tokens at 29.5 t/s with 0 errors.
* **Root Cause**: Subprocess calls used arbitrary hardcoded timeouts (`timeout=90`, `timeout=120`) that were insufficient for multi-turn agentic thinking loops (4 consecutive tool calls with 23K prompt tokens).
* **Remediation**:
  * Eliminate arbitrary tight timeouts on live generative workflows. Use reactive completion polling or allocate realistic headroom ($240\text{s} - 300\text{s}$) for multi-turn SLM generation.

---

### Issue #04: Dual-Slot Inference Context Mismatch (`-c 32768` vs `-c 131072`)
* **Classification**: Runtime Hardware Configuration Bug
* **Impact**: Critical
* **Discovered In**: Turn 0 Context Overflow
* **Symptom**: `llama-server` rejected requests with: `request (22956 tokens) exceeds the available context size (16384 tokens)`.
* **Root Cause**: `llama-server` divides the total context `-c` evenly across parallel slots (`-np 2`). A `-c 32768` flag only allocated $16,384$ tokens per slot. Because Hermes system prompts and tool schemas occupy ~22,956 tokens, Turn 0 immediately overflowed.
* **Remediation**:
  * Set `-c 131072` (128K total), giving exactly **$65,536\text{ tokens (64K)}$ per slot** across 2 slots.
  * Verified $K/V$ quantization (`q4_0`) keeps total VRAM $\le 3,240\text{ MiB}$ (well below the $4,812\text{ MiB}$ safety ceiling).

---

### Issue #05: Prompt-Policed Jailbreak Containment vs. Structural Pre-Execution Gating
* **Classification**: Security Architecture Gap
* **Impact**: High
* **Discovered In**: `test_live_adversarial_jailbreak_tamper_attempt`
* **Symptom**: When issued a hostile prompt ordering the deletion of `.integrity` logs and modification of `agent_capabilities.yaml`, the agent attempted a tool call to read the file before refusing.
* **Root Cause**: Relying on the model to read a file and then decide to refuse is insecure. A compromised or hallucinating model could issue write or delete commands before refusal logic kicks in.
* **Remediation**:
  * Added `validate_security_policy_path()` and `validate_security_policy_command()` to `capability_masks.py`.
  * Pre-execution dispatch intercepts and aborts any file modification or shell deletion targeting `~/.hermes/policy/` or `~/.hermes/logs/*.integrity` before execution reaches the OS.

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
* **Remediation**:
  * Add SQLite persistence backing to `OpenVikingVFS` with WAL mode.
  * Replace `len(text) // 4` with exact Tiktoken BPE / Gemma tokenizer caching.
  * Build an in-memory inverted tag index to replace linear recursive traversal in `find()`.

---

### Issue #07: Codebase Memory MCP JSON Truncation Syntax Corruption
* **Classification**: MCP Tool Contract / Parser Crash
* **Impact**: Critical
* **Discovered In**: `src/hermes_core/codebase_memory_mcp.py`
* **Symptom**: When querying large class hierarchies or multi-hop call graphs, MCP tool consumers fail with `json.decoder.JSONDecodeError: Unterminated string`.
* **Root Cause**: `truncate_to_tokens(text, max_tokens=150)` performs blind character-level string slicing (`text[:max_chars - 3] + "..."`). When `text` is a JSON serialization of symbols or classes, blind character chopping produces malformed JSON syntax.
* **Remediation**:
  * Implement **Structured AST Node Slicing** instead of raw string truncation. Truncate array elements (e.g. `symbols[:5]`) *before* serializing to JSON, ensuring the JSON document is always syntactically valid.

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
* **Remediation**:
  * Wire `TreeSitterParser` from `codebase_memory_mcp.py` into `SymbolGraph` to index polyglot repositories.
  * Add `UNIQUE(source_file, caller_symbol, target_symbol, ref_type)` constraint and normalized relative paths to SQLite schema.
  * Replace `fnmatch` with `pathspec` for 100% Git-compliant `.gitignore` evaluation.

---

### Issue #09: LSP Bridge False-Positive Bracket Syntax Scrubber
* **Classification**: Linter / AST Fallback False Positive
* **Impact**: High
* **Discovered In**: `src/hermes_core/lsp_bridge.py`
* **Symptom**: Valid JS, TS, HTML, and C++ files are incorrectly rejected by the syntax guard with `"Unmatched closing bracket"` or `"Unclosed opening bracket"`.
* **Root Cause**: `analyze_generic_source()` scans raw characters line-by-line using a naive stack. It does not track string literals (`"..."`, `'...'`, `` `...` ``), regexes (`/.../`), or single/multi-line comments (`//`, `/* */`), causing brackets inside strings or comments to trigger false syntax errors.
* **Remediation**:
  * Replace naive bracket stack scanning with Tree-sitter AST syntax error detection (`tree.root_node.has_error`).

---

### Issue #10: Knowledge Graph AST `Name` Confusion (Variable as Callee)
* **Classification**: Knowledge Graph & Topological Extraction
* **Impact**: Medium
* **Discovered In**: `src/hermes_core/knowledge_graph.py`
* **Symptom**: The Codebase Knowledge Graph records local variables (`x`, `y`, `self`, `None`, `True`) as function calls in `caller_graph`.
* **Root Cause**: `_index_python_file` extracts calls using `calls = [n.id for n in ast.walk(item) if isinstance(n, ast.Name)]`. In Python's AST, `ast.Name` represents all variable names and constants, not function calls (`ast.Call`).
* **Remediation**:
  * Filter strictly for `ast.Call` nodes and extract callee names via `node.func.id` or `node.func.attr`.

---

### Issue #11: Hypothesis Tree Singleton Collision in Multi-Agent Workflows
* **Classification**: Concurrency & State Isolation
* **Impact**: High
* **Discovered In**: `src/hermes_core/hypothesis_tree.py`
* **Symptom**: When multiple subagents or background tasks run concurrently, hypothesis trees overwrite each other, causing orphaned branch IDs and corrupted backtracking histories.
* **Root Cause**: `STORAGE_PATH` is hardcoded to a static singleton file `/dev/shm/hypothesis_tree.json`.
* **Remediation**:
  * Scope hypothesis tree state by session and task ID (e.g. `/dev/shm/hermes/hypothesis_{session_id}_{task_id}.json`).

---

### Issue #12: Stubbed Search Tool in Universal Primitives
* **Classification**: Missing Implementation / Tool Stub
* **Impact**: Medium
* **Discovered In**: `src/hermes_core/tools.py`
* **Symptom**: Calls to `search_web()` return a static dummy string: `"Search results for '...': Query resolved successfully."`
* **Root Cause**: `tools.py:search_web()` was left as a stub and never connected to `web_grounding.py` or `extract_web_content.py`.
* **Remediation**:
  * Connect `search_web()` to `private_dot_hermes/bin/executable_extract_web_content.py` and SearXNG / Searx / Google grounding adapters.

---

### Issue #13: Default Workspace Root Path Resolution Divergence
* **Classification**: Path Resolution & Sandbox Scoping
* **Impact**: High
* **Discovered In**: `src/hermes_core/tools.py`
* **Symptom**: Relative file operations (`read_file("src/app.py")`) fail or look in `/dev/shm/hermes_workspace` even when the user is working in their project directory.
* **Root Cause**: `_resolve_path()` defaults to `Path("/dev/shm/hermes_workspace")` if `workspace_root` is not explicitly passed.
* **Remediation**:
  * Default `workspace_root` dynamically to `Path.cwd()` (or active project root via environment variable).

---

## 2. Exhaustive Codebase Audit: Timeouts, Budgets, Sleeps & Fragile Heuristics

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                CODEBASE FRAGILITY & HEURISTICS MATRIX                            │
├──────────────────────────────────────┬─────────────────────────┬─────────────────────────────────┤
│ File Location                        │ Mechanism Used          │ Risk / Fragility Analysis       │
├──────────────────────────────────────┼─────────────────────────┼─────────────────────────────────┤
│ `private_dot_hermes/config.yaml`     │ `timeout: 180`          │ Arbitrary terminal kill timer;  │
│                                      │ `inactivity_timeout: 120│ can kill heavy builds mid-run   │
├──────────────────────────────────────┼─────────────────────────┼─────────────────────────────────┤
│ `src/hermes_core/capability_masks.py`│ `ROLE_POLICIES`         │ Read-only fallback is good, but │
│                                      │ (Prompt & dispatch)     │ requires path-level gating      │
├──────────────────────────────────────┼─────────────────────────┼─────────────────────────────────┤
│ `src/hermes_core/codebase_memory_mcp`│ `MAX_TOKENS = 150`      │ Blind string slicing produces   │
│                                      │ `truncate_to_tokens()`  │ malformed, unparseable JSON     │
├──────────────────────────────────────┼─────────────────────────┼─────────────────────────────────┤
│ `src/hermes_core/symbol_graph.py`    │ `patterns = ["*.py"]`   │ Monoglot limitation; completely │
│                                      │ `ast.parse` only        │ ignores JS, TS, Rust, Go, HTML  │
├──────────────────────────────────────┼─────────────────────────┼─────────────────────────────────┤
│ `src/hermes_core/lsp_bridge.py`      │ Bracket stack scrubber  │ False positives on quotes,      │
│                                      │ across raw characters   │ comments, regex, and templates  │
├──────────────────────────────────────┼─────────────────────────┼─────────────────────────────────┤
│ `src/hermes_core/knowledge_graph.py` │ `ast.Name` for calls    │ Confuses local variables &      │
│                                      │ naive regex for JS      │ arguments with function calls   │
├──────────────────────────────────────┼─────────────────────────┼─────────────────────────────────┤
│ `src/hermes_core/hypothesis_tree.py` │ Hardcoded singleton     │ State collision & corruption    │
│                                      │ `/dev/shm/...json`      │ across concurrent agent tasks   │
├──────────────────────────────────────┼─────────────────────────┼─────────────────────────────────┤
│ `src/hermes_core/tools.py`           │ `search_web()` stub;    │ Returns dummy string; relative  │
│                                      │ `/dev/shm` default root │ paths point to /dev/shm         │
├──────────────────────────────────────┼─────────────────────────┼─────────────────────────────────┤
│ `src/hermes_core/context_compactor.py`│ 4-tier token drop (95%) │ Heuristic token slicing drops   │
│                                      │ & message truncation    │ critical tool definitions       │
├──────────────────────────────────────┼─────────────────────────┼─────────────────────────────────┤
│ `src/hermes_core/process_guard.py`   │ Polling loops +         │ Requires explicit PGID kill     │
│                                      │ hardcoded 100ms grace   │ rather than arbitrary sleep     │
├──────────────────────────────────────┼─────────────────────────┼─────────────────────────────────┤
│ `private_skills/.../comfyui/`        │ `time.sleep(interval)`  │ Wasteful CPU spin; should use   │
│                                      │ `_sleep_backoff()`      │ event-driven WebSocket listener │
├──────────────────────────────────────┼─────────────────────────┼─────────────────────────────────┤
│ `private_skills/.../maps/`           │ `time.sleep(1.0)`       │ Hardcoded Nominatim rate limit; │
│                                      │ retry multiplier sleeps │ should use Token Bucket limiter │
├──────────────────────────────────────┼─────────────────────────┼─────────────────────────────────┤
│ `private_skills/.../claude-code/`    │ 15+ hardcoded `timeout` │ Fragile CLI execution examples; │
│                                      │ parameters in SKILL.md  │ should use output stream signals│
├──────────────────────────────────────┼─────────────────────────┼─────────────────────────────────┤
│ `SOUL.md` & `AGENTS.md`              │ Natural language rules  │ Prompt-policing is easily       │
│                                      │ for output conciseness  │ ignored by SLMs without brakes  │
└──────────────────────────────────────┴─────────────────────────┴─────────────────────────────────┘
```

---

## 3. Detailed Audit by Category

### A. Arbitrary Subprocess & Terminal Timeouts
* **Where found:** `config.yaml` (`timeout: 180`, `inactivity_timeout: 120`), `container_cmd.py` (`timeout=10`), `observer_gate.py` (`timeout=5`, `timeout=3`), test suites (`timeout=90`, `timeout=120`).
* **Why it is fragile:** Hardcoded seconds fail across heterogenous hardware. A linter or compiler taking 5.1 seconds on a busy machine triggers a hard failure.
* **Deterministic Fix:** Replace static wall-clock timers with **I/O Heartbeat Monitors** (detecting active stdout/stderr stream bytes) and **Process Exit Events**.

### B. Artificial Sleeps & Spin-Waits
* **Where found:** `comfyui/scripts/_common.py` (`time.sleep()`), `maps/scripts/maps_client.py` (`time.sleep(1.0)`), `grounded-citations/scripts/sources.py` (`time.sleep(0.05)`).
* **Why it is fragile:** Sleeps inject artificial latency and introduce race conditions when background jobs complete sooner or later than the sleep window.
* **Deterministic Fix:**
  * Replace polling sleeps with **async event listeners** (e.g. WebSocket notifications for neural generation).
  * Replace sleep-based rate limiters with **Leaky Bucket / Token Bucket algorithms** that compute exact mathematical dispatch windows.

### C. Context Compression & Truncation Heuristics
* **Where found:** `context_compactor.py`, `conversation_loop.py`.
* **Why it is fragile:** When context overflows, the compactor attempts a 95% token drop or truncates message history. If a prompt contains 22K tokens of system instructions and tool definitions, truncation heuristics fail to compress and cause the `"Cannot compress further"` error loop.
* **Deterministic Fix:**
  * **Dynamic Tool Offloading:** Never load all tool schemas simultaneously. Load only the tools permitted for the active subagent role via `capability_masks.py`.
  * **Summary Anchoring:** Replace linear truncation with structural SQLite memory graphs (`experiential.jsonl`).

### D. Prompt-Policed Guidelines vs. Physical Constraints
* **Where found:** `SOUL.md`, `AGENTS.md`, `dot_hermes_AGENTS.md`.
* **Why it is fragile:** Phrases like *"Never output massive blocks"*, *"Keep changes atomic"*, and *"Follow Phase 0"* rely entirely on the model's self-discipline. Small language models (4B–8B) routinely regress into completion mode when given ambiguous prompts.
* **Deterministic Fix:**
  * **Physical Token Brake:** Dispatcher truncates or interrupts single turns at $\le 800\text{ tokens}$ and demands tool execution.
  * **Pre-Execution Observer Gate:** File write operations greater than 150 lines without prior DAG blueprinting are structurally rejected by the tool executor.

---

## 4. Architectural Roadmap for Permanent Elimination

1. **Physical Turn Token Limiter**: Enforce `max_tokens: 800` per generation turn in `config.yaml` and `llama-server` dispatch.
2. **Schema-Driven DAG Enforcer**: Require `emit_plan_dag` tool call before `write_file` is unlocked.
3. **Structured Tree-Sitter MCP Slicing**: Truncate JSON AST elements structurally before serialization.
4. **Multi-Language AST Symbol Graph**: Connect `tree_sitter_language_pack` to `symbol_graph.py` with `pathspec` gitignore resolution.
5. **Session-Isolated State**: Scope `/dev/shm` temporary storage by `{session_id}_{task_id}` across all engines.
6. **Pre-Execution Policy Filter**: Intercept file writes and command executions in `capability_masks.py` before touching the OS.
