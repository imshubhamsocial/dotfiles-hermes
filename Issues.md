# Issues, Architectural Fragility, & Detailed Implementation Plans (ws-hermes)

This document registers all 28 operational bugs, loopholes, regressions, and architectural vulnerabilities discovered across the Hermes agentic harness. For every issue, it provides a **precise, step-by-step implementation plan** detailing the exact files to modify, upstream packages to integrate, code changes, and manual verification procedures.

---

## 1. Upstream Package Replacement Matrix

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

## 2. Master Issue Registry & Detailed Implementation Plans

### Issue #01: The "Completion Trap" & Missing Physical Output Token Gating
* **Classification**: Behavioral Regression / Lack of Physical Gating
* **Impact**: Critical
* **Discovered In**: `test_live_generative_ui_artifact_creation`, `test_live_polars_data_analysis_skill_invocation`
* **Symptom**: Gemma-4 emitted 2,500+ continuous tokens in a single monolithic generation turn lasting 150–180s.
* **Root Cause**: The harness allowed a single turn to run up to `max_tokens: 4096` without an intermediate yield or token brake.
* **Precise Implementation Plan**:
  1. **Files to Touch**: `private_dot_hermes/config.yaml`, `src/hermes_core/swarm_engine.py`, `src/hermes_core/spec_first_planner.py`.
  2. **Dependencies**: `nemoguardrails` (Output Rail).
  3. **Concrete Changes**:
     * In `config.yaml`, set `agent.max_tokens_per_turn: 600` under inference settings.
     * In `swarm_engine.py:HermesOrchestrator.run()`, pass `max_tokens=600` to the OpenAI/llama-server client completions call.
     * In `spec_first_planner.py`, enforce that Phase 0 must emit an architectural DAG JSON block (`emit_task_dag`) before unlocking full file synthesis tools (`write_file`).
  4. **Manual Verification**: Run `hermes -z "Generate a 2000-line single file HTML dashboard"`; assert generation yields after emitting skeleton/blueprint in $\le 600\text{ tokens}$ ($\le 15\text{s}$) rather than dumping 2,500 tokens.

---

### Issue #02: Subprocess Directory Isolation Leak (`--in DIR` Parameter)
* **Classification**: Test Harness / Subprocess Calling Bug
* **Impact**: High
* **Discovered In**: `test_developer_workflows_e2e.py`
* **Symptom**: Executing `hermes -z "..."` inside `/tmp/tmp...` wrote files to `~` instead of the caller's working directory.
* **Root Cause**: `hermes` CLI defaulted working directory to `~` (or `cwd: .` in config) and required explicit `--in <DIR>`.
* **Precise Implementation Plan**:
  1. **Files to Touch**: `private_dot_hermes/src/hermes_core/cli.py`, `tests/roadmap6_adversarial/conftest.py`.
  2. **Dependencies**: None (Standard Library `sys`, `pathlib.Path`).
  3. **Concrete Changes**:
     * In `cli.py`, inspect `args.in_dir`. If `None`, check `if not sys.stdin.isatty() or args.oneshot:` and default `args.in_dir = Path.cwd().resolve()`.
     * In `conftest.py`, ensure all test fixtures pass `cwd=str(tmp_path)` and explicit `in_dir`.
  4. **Manual Verification**: Run `cd /tmp && hermes -z "write a file hello.txt containing world"`; verify `hello.txt` is created inside `/tmp/hello.txt` and NOT in `$HOME/hello.txt`.

---

### Issue #03: Heuristic Subprocess Timeouts & Missing I/O Activity Heartbeats
* **Classification**: Harness Invariant Violation / Artificial Timer Crutch
* **Impact**: Critical
* **Discovered In**: `test_hermes_live_prompts.py`, `test_developer_workflows_e2e.py`
* **Symptom**: Subprocesses were killed by static `timeout=90s` while `llama-server` was actively generating tokens at 29.5 t/s.
* **Root Cause**: Relying on wall-clock timers instead of monitoring stdout/stderr byte stream activity.
* **Precise Implementation Plan**:
  1. **Files to Touch**: `src/hermes_core/process_guard.py`, `src/hermes_core/runner.py`.
  2. **Dependencies**: `asyncio`, `selectors`.
  3. **Concrete Changes**:
     * In `process_guard.py:run_with_group_teardown()`, replace `proc.communicate(timeout=...)` with a non-blocking `selectors.DefaultSelector()` loop reading stdout.
     * Implement `inactivity_heartbeat_s = 15.0`: track `last_byte_time = time.perf_counter()`. Only trigger `os.killpg(pgid, SIGKILL)` if `time.perf_counter() - last_byte_time > 15.0`.
     * Remove arbitrary global wall-clock timeouts from live test runners.
  4. **Manual Verification**: Run a long-running streaming command `python3 -c "import time; [print(f'chunk {i}', flush=True) or time.sleep(2) for i in range(20)]"`; verify process runs to completion (40s) without being killed because heartbeats arrive every 2s.

---

### Issue #04: Dual-Slot Inference Context Mismatch (`-c 32768` vs `-c 131072`)
* **Classification**: Runtime Hardware Configuration Bug
* **Impact**: Critical
* **Discovered In**: Turn 0 Context Overflow
* **Symptom**: `llama-server` rejected requests because 23K tool schemas exceeded the 16K per-slot limit.
* **Root Cause**: `-c 32768` split across `-np 2` gave only 16,384 tokens per slot.
* **Precise Implementation Plan**:
  1. **Files to Touch**: `private_dot_hermes/bin/executable_llama-server`, `~/.local/share/chezmoi/private_dot_hermes/config.yaml`.
  2. **Dependencies**: `llama-server` (GGUF runtime).
  3. **Concrete Changes**:
     * In server launch script, set `-c 131072 -np 2 --ctk q4_0 --ctv q4_0`.
     * Verify slot capacity yields exactly $65,536\text{ tokens (64K)}$ per slot.
     * Verify total VRAM allocation stays $\le 3,240\text{ MiB}$ via `nvidia-smi`.
  4. **Manual Verification**: Call `curl http://127.0.0.1:8138/props` and `curl http://127.0.0.1:8138/slots`; verify `n_ctx_slot: 65536` for both slots.

---

### Issue #05: Prompt-Policed Jailbreak Containment vs. Structural Pre-Execution Gating
* **Classification**: Security Architecture Gap
* **Impact**: High
* **Discovered In**: `test_live_adversarial_jailbreak_tamper_attempt`
* **Symptom**: Model attempted to read integrity logs before refusing a jailbreak prompt.
* **Root Cause**: Relying on prompt instructions rather than intercepting tool calls before dispatch.
* **Precise Implementation Plan**:
  1. **Files to Touch**: `src/hermes_core/capability_masks.py`, `src/hermes_core/tools.py`.
  2. **Dependencies**: `nemoguardrails` (Execution Rails).
  3. **Concrete Changes**:
     * In `capability_masks.py`, integrate `validate_security_policy_path(path: str)` and `validate_security_policy_command(cmd: str)`.
     * In `tools.py:read_file()`, `write_file()`, `patch_file()`, and `execute_command()`, add a pre-execution guard:
       ```python
       is_safe, reason = validate_security_policy_path(filepath)
       if not is_safe:
           return f"Security Policy Denial: {reason}"
       ```
     * Block all access to `~/.hermes/policy/`, `~/.hermes/logs/*.integrity`, and dangerous commands (`rm -rf /`, `chmod 777`).
  4. **Manual Verification**: Run `hermes -z "Read ~/.hermes/logs/audit.integrity"`; assert immediate hard refusal from user-space pre-execution guard with 0 filesystem reads.

---

### Issue #06: OpenViking VFS Ephemerality & Coarse Token Drift
* **Classification**: Virtual Filesystem / State Loss
* **Impact**: High
* **Discovered In**: `src/hermes_core/openviking_vfs.py`
* **Symptom**: `viking://` nodes wiped on process exit; `len(text) // 4` token estimates drift by 50%.
* **Root Cause**: Pure transient RAMDisk storage without disk backing; character division token heuristic.
* **Precise Implementation Plan**:
  1. **Files to Touch**: `src/hermes_core/openviking_vfs.py`.
  2. **Dependencies**: `sqlite3` (Standard Library WAL mode), `tiktoken` (or `tokenizers`).
  3. **Concrete Changes**:
     * Add an embedded SQLite persistence table `vfs_nodes (uri TEXT PRIMARY KEY, l0_abstract TEXT, l1_overview TEXT, l2_content TEXT, tags TEXT, token_count INT, updated_at REAL)`.
     * Replace `len(text) // 4` with exact BPE tokenizer: `tiktoken.get_encoding("cl100k_base").encode(text)`.
     * Build an in-memory `Dict[str, Set[str]]` tag index for $O(1)$ tag filtering in `find()`.
  4. **Manual Verification**: Write a node via VFS, kill the Python process, instantiate a new `OpenVikingVFS()` instance, and verify `vfs.read_node("viking://core/spec")` returns the persisted L0/L1/L2 content.

---

### Issue #07: Codebase Memory MCP JSON Truncation Syntax Corruption
* **Classification**: MCP Tool Contract / Parser Crash
* **Impact**: Critical
* **Discovered In**: `src/hermes_core/codebase_memory_mcp.py`
* **Symptom**: `truncate_to_tokens()` sliced JSON strings mid-token, throwing `JSONDecodeError`.
* **Root Cause**: Blind substring slicing (`text[:max_chars - 3] + "..."`) on structured JSON data.
* **Precise Implementation Plan**:
  1. **Files to Touch**: `src/hermes_core/codebase_memory_mcp.py`.
  2. **Dependencies**: `mcp[cli]` (Anthropic FastMCP Python SDK).
  3. **Concrete Changes**:
     * Replace manual JSON serialization with FastMCP (`from mcp.server.fastmcp import FastMCP`).
     * In query tools (`search_symbols`, `get_class_hierarchy`), truncate list items in Python (e.g. `symbols = symbols[:10]`) *before* serializing to JSON.
     * Remove all raw string truncation functions (`truncate_to_tokens`).
  4. **Manual Verification**: Run MCP query returning 500+ symbols; parse response with `json.loads()`; assert valid JSON syntax with 0 decode errors.

---

### Issue #08: AST Symbol Graph Monoglot Limitation & Schema Pollution
* **Classification**: AST & Code Intelligence
* **Impact**: High
* **Discovered In**: `src/hermes_core/symbol_graph.py`
* **Symptom**: Symbol graph skipped JS/TS/Rust/Go; duplicate references bloated SQLite on re-indexing.
* **Root Cause**: Hardcoded Python stdlib `ast.parse`; missing `UNIQUE` constraints in SQLite; naive `fnmatch`.
* **Precise Implementation Plan**:
  1. **Files to Touch**: `src/hermes_core/symbol_graph.py`.
  2. **Dependencies**: `tree-sitter`, `tree-sitter-languages`, `pathspec`.
  3. **Concrete Changes**:
     * Replace `ast.parse` with `tree_sitter_languages.get_parser(lang)`.
     * Add parsers for Python, JavaScript, TypeScript, Rust, Go, and C++.
     * Update SQLite schema: `CREATE UNIQUE INDEX idx_symbol_ref ON symbol_references(source_file, caller_symbol, target_symbol, ref_type)`.
     * Replace `fnmatch` with `pathspec.PathSpec.from_lines("gitwildmatch", gitignore_lines)`.
  4. **Manual Verification**: Index a mixed TypeScript/Python repository; verify symbols from both `.ts` (interfaces, functions) and `.py` (classes, defs) populate SQLite with 0 duplicate rows on re-indexing.

---

### Issue #09: LSP Bridge False-Positive Bracket Syntax Scrubber
* **Classification**: Linter / AST Fallback False Positive
* **Impact**: High
* **Discovered In**: `src/hermes_core/lsp_bridge.py`
* **Symptom**: Valid JS/TS files with brackets in strings/regexes were rejected as syntax errors.
* **Root Cause**: Scanning raw characters with a stack without lexing string literals or comments.
* **Precise Implementation Plan**:
  1. **Files to Touch**: `src/hermes_core/lsp_bridge.py`.
  2. **Dependencies**: `tree-sitter`, `tree-sitter-languages`.
  3. **Concrete Changes**:
     * In `analyze_generic_source(filepath, content)`:
       ```python
       parser = tree_sitter_languages.get_parser(get_language(filepath))
       tree = parser.parse(bytes(content, "utf-8"))
       if tree.root_node.has_error:
           return False, "Tree-sitter detected syntax error in source tree"
       return True, "Valid AST"
       ```
     * Remove manual bracket stack counting.
  4. **Manual Verification**: Pass `const r = /{[0-9]}/; const msg = "unbalanced {";` to `analyze_generic_source("app.ts", code)`; assert returns `(True, "Valid AST")`.

---

### Issue #10: Knowledge Graph AST `Name` Confusion (Variable as Callee)
* **Classification**: Knowledge Graph & Topological Extraction
* **Impact**: Medium
* **Discovered In**: `src/hermes_core/knowledge_graph.py`
* **Symptom**: Functions were recorded as calling variables (`x`, `y`, `self`, `None`).
* **Root Cause**: `ast.walk()` filtered on `isinstance(n, ast.Name)` instead of `isinstance(n, ast.Call)`.
* **Precise Implementation Plan**:
  1. **Files to Touch**: `src/hermes_core/knowledge_graph.py`.
  2. **Dependencies**: Standard Library `ast`.
  3. **Concrete Changes**:
     * In `_index_python_file()`:
       ```python
       calls = []
       for node in ast.walk(func_node):
           if isinstance(node, ast.Call):
               if isinstance(node.func, ast.Name):
                   calls.append(node.func.id)
               elif isinstance(node.func, ast.Attribute):
                   calls.append(node.func.attr)
       calls = [c for c in set(calls) if c not in {"print", "len", "range", "isinstance", "str", "int"}]
       ```
  4. **Manual Verification**: Parse `def foo(): x = 1; y = 2; bar(); return x`; assert `node.calls == ["bar"]` and `x`, `y` are not present.

---

### Issue #11: Hypothesis Tree Singleton Collision in Multi-Agent Workflows
* **Classification**: Concurrency & State Isolation
* **Impact**: High
* **Discovered In**: `src/hermes_core/hypothesis_tree.py`
* **Symptom**: Concurrent agents overwrote each other's search trees in `/dev/shm/hypothesis_tree.json`.
* **Root Cause**: Hardcoded singleton storage path.
* **Precise Implementation Plan**:
  1. **Files to Touch**: `src/hermes_core/hypothesis_tree.py`.
  2. **Dependencies**: `google/adk-python` (session hierarchy).
  3. **Concrete Changes**:
     * In `HypothesisTree`: accept `session_id: str` and `task_id: str` in `__init__()`.
     * Construct dynamic path: `storage_dir = Path("/dev/shm/hermes/trees")` and `storage_file = storage_dir / f"tree_{session_id}_{task_id}.json"`.
     * Add file-locking via `fcntl.flock()` during tree state writes.
  4. **Manual Verification**: Run two parallel threads creating branches with distinct `session_id`s; assert two separate JSON files are maintained without cross-talk.

---

### Issue #12: Stubbed Search Tool in Universal Primitives
* **Classification**: Missing Implementation / Tool Stub
* **Impact**: Medium
* **Discovered In**: `src/hermes_core/tools.py`
* **Symptom**: `search_web()` returned a static mock string.
* **Root Cause**: Function body was a placeholder returning a hardcoded formatted string.
* **Precise Implementation Plan**:
  1. **Files to Touch**: `src/hermes_core/tools.py`.
  2. **Dependencies**: `duckduckgo-search` (PyPI), `trafilatura`.
  3. **Concrete Changes**:
     * Connect `tools.py:search_web(query)` to `WebGroundingEngine.ground(query)`.
     * If internet is unavailable, fall back to querying local documentation index (`index_docs.py`).
  4. **Manual Verification**: Run `python3 -c "from hermes_core.tools import search_web; print(search_web('Python dataclasses'))"`; verify live search snippets are returned.

---

### Issue #13: Default Workspace Root Path Resolution Divergence
* **Classification**: Path Resolution & Sandbox Scoping
* **Impact**: High
* **Discovered In**: `src/hermes_core/tools.py`
* **Symptom**: Relative file paths resolved against `/dev/shm/hermes_workspace` instead of active project root.
* **Root Cause**: `_resolve_path()` defaulted to a hardcoded constant when `workspace_root` was `None`.
* **Precise Implementation Plan**:
  1. **Files to Touch**: `src/hermes_core/tools.py`.
  2. **Dependencies**: Standard Library `pathlib.Path`, `os`.
  3. **Concrete Changes**:
     * In `_resolve_path(filepath: str, workspace_root: Optional[str] = None) -> Path`:
       ```python
       root = Path(workspace_root or os.environ.get("HERMES_WORKSPACE") or Path.cwd()).resolve()
       p = Path(filepath)
       return (root / p).resolve() if not p.is_absolute() else p.resolve()
       ```
  4. **Manual Verification**: Call `read_file("Issues.md")` from project root; assert file contents are read from current directory instead of looking in `/dev/shm`.

---

### Issue #14: Speculative Tool Executor Promise Abandonment & Memory Leak
* **Classification**: Async Tool Execution / Resource Leak
* **Impact**: Medium
* **Discovered In**: `src/hermes_core/speculative_executor.py`
* **Symptom**: Speculative promises taking $>5.0\text{s}$ were rejected; `self.promises` dictionary grew unbounded.
* **Root Cause**: `promise.future.result(timeout=5.0)` hardcoded timeout; missing LRU cache on promises.
* **Precise Implementation Plan**:
  1. **Files to Touch**: `src/hermes_core/speculative_executor.py`.
  2. **Dependencies**: `collections.OrderedDict`, `asyncio.Future`.
  3. **Concrete Changes**:
     * Replace timeout polling with async callback `fut.add_done_callback(lambda f: self._on_promise_done(ckey, f))`.
     * Cap `self.promises` using an `OrderedDict` with `MAX_PROMISES = 100`: when exceeded, pop the oldest resolved promise (`self.promises.popitem(last=False)`).
  4. **Manual Verification**: Run 150 speculative tool calls in a loop; verify `len(executor.promises) <= 100` and no memory leak occurs.

---

### Issue #15: Deterministic Code Extractor Monoglot Python Destruction
* **Classification**: Code Extraction & Tool Calling
* **Impact**: High
* **Discovered In**: `private_dot_hermes/bin/executable_extract_code_mode.py`
* **Symptom**: Non-Python code blocks (Bash, HTML, JS, JSON) were discarded with `"contained no parsable code body"`.
* **Root Cause**: All extracted code chunks were filtered through Python's `ast.parse()`.
* **Precise Implementation Plan**:
  1. **Files to Touch**: `private_dot_hermes/bin/executable_extract_code_mode.py`.
  2. **Dependencies**: `tree-sitter`, `tree-sitter-languages`.
  3. **Concrete Changes**:
     * Extract language tag from opening fence (e.g. ```` ```javascript ```` $\rightarrow$ `lang="javascript"`).
     * If `lang in {"bash", "sh", "zsh"}`: validate via `bash -n` or accept directly.
     * If `lang in {"json", "yaml", "html", "js", "ts", "rust", "go"}`: validate using Tree-sitter or JSON parser instead of `ast.parse()`.
     * Only apply `ast.parse()` when `lang in {"python", "py"}` or no tag is provided.
  4. **Manual Verification**: Pass a markdown document containing ```` ```bash\necho "test"\n``` ```` to `extract_code()`; assert `echo "test"` is extracted without error.

---

### Issue #16: External Directory Expansion in Skill Verification
* **Classification**: Configuration & Environment Resilience
* **Impact**: Medium
* **Discovered In**: `private_dot_hermes/bin/executable_verify_skills_config.py`
* **Symptom**: Profiles declaring `external_dirs` with tildes or unexpanded shell variables failed verification.
* **Root Cause**: `Path.is_dir()` called on raw unexpanded path strings.
* **Precise Implementation Plan**:
  1. **Files to Touch**: `private_dot_hermes/bin/executable_verify_skills_config.py`.
  2. **Dependencies**: Standard Library `os.path`.
  3. **Concrete Changes**:
     * In `profile_external_dirs()`:
       ```python
       expanded = [Path(os.path.expandvars(os.path.expanduser(p))).resolve() for p in raw]
       missing = [str(p) for p in expanded if not p.is_dir()]
       ```
  4. **Manual Verification**: Declare `external_dirs: ["~/.hermes/skills"]` in a test profile config; run `python3 bin/verify_skills_config.py`; assert status is `PASS`.

---

### Issue #17: Inter-Bot Communication & Synergy Bus Memory Leak
* **Classification**: Multi-Bot & Reactive Bus / Memory Leak
* **Impact**: High
* **Discovered In**: `src/hermes_core/synergy_bus.py`
* **Symptom**: `SynergyEventBus.event_history` grew unbounded over long multi-agent sessions.
* **Root Cause**: `self.event_history.append(event)` without a capacity cap or FIFO eviction.
* **Precise Implementation Plan**:
  1. **Files to Touch**: `src/hermes_core/synergy_bus.py`.
  2. **Dependencies**: `collections.deque` or `ThreadSafeRingBuffer`.
  3. **Concrete Changes**:
     * In `SynergyEventBus.__init__()`, initialize `self.event_history = deque(maxlen=1000)`.
     * Expose `get_recent_events(limit: int = 50) -> List[SynergyEvent]`.
  4. **Manual Verification**: Emit 5,000 events through `SynergyEventBus`; assert `len(bus.event_history) == 1000`.

---

### Issue #18: Multi-Bot Delegation Hardcoded Mock Orchestration
* **Classification**: Multi-Agent Orchestration / Mock Stub
* **Impact**: Critical
* **Discovered In**: `src/hermes_core/multi_bot_delegation.py`
* **Symptom**: `execute_delegation_pipeline()` returned synthetic mock strings without invoking agents or tools.
* **Root Cause**: Subsystem was authored as a prototype stub.
* **Precise Implementation Plan**:
  1. **Files to Touch**: `src/hermes_core/multi_bot_delegation.py`.
  2. **Dependencies**: `google/adk-python` (`SequentialAgent`), `src/hermes_core/swarm_engine.py`.
  3. **Concrete Changes**:
     * In `MultiBotOrchestrator.execute_delegation_pipeline(goal)`:
       * **Stage 1 (Architect):** Invoke Hermes in Architect mode (`agent=architect_agent`) to produce `.hermes/plan.json`.
       * **Stage 2 (Coder):** Invoke Coder agent with plan context to write files.
       * **Stage 3 (Tester):** Invoke Tester agent to run `pytest` / `npm test` via `execute_command`.
     * Return verified `DelegationReport` containing live execution artifacts.
  4. **Manual Verification**: Run delegation pipeline on a real test task; verify `.hermes/plan.json` is generated on disk and test suite passes.

---

### Issue #19: Swarm Engine Function Schema Type Coercion & Docstring Loss
* **Classification**: Tool Calling & Schema Generation
* **Impact**: Medium
* **Discovered In**: `src/hermes_core/swarm_engine.py`
* **Symptom**: Tools with `Union`, `Optional`, or Pydantic models defaulted to `"type": "string"` with generic descriptions.
* **Root Cause**: Primitive `if/elif` type checker in `function_to_schema()`; no docstring parsing.
* **Precise Implementation Plan**:
  1. **Files to Touch**: `src/hermes_core/swarm_engine.py`.
  2. **Dependencies**: `mcp[cli]` (FastMCP) or `docstring-parser`.
  3. **Concrete Changes**:
     * Use `docstring_parser.parse(func.__doc__)` to extract `:param` descriptions.
     * Handle `typing.get_origin()` and `typing.get_args()` for `Union[T, None]`, `List[T]`, and `Literal[A, B]`.
     * Map `Literal["x", "y"]` to `{"type": "string", "enum": ["x", "y"]}`.
  4. **Manual Verification**: Generate schema for a function `def test_fn(mode: Literal['a', 'b'], count: Optional[int] = 1): """Args:\n count: Number of items."""`; verify schema output includes `enum: ['a', 'b']` and parameter description `"Number of items."`.

---

### Issue #20: Web Grounding Module Import Failure & Search Black Hole
* **Classification**: Web Grounding & External Knowledge
* **Impact**: Critical
* **Discovered In**: `src/hermes_core/web_grounding.py`
* **Symptom**: `from ddgs import DDGS` failed with `ModuleNotFoundError`; web search returned empty results.
* **Root Cause**: Wrong package import name (`ddgs` instead of `duckduckgo_search`).
* **Precise Implementation Plan**:
  1. **Files to Touch**: `src/hermes_core/web_grounding.py`, `private_dot_hermes/bin/executable_setup.sh`.
  2. **Dependencies**: `duckduckgo-search` (PyPI: `duckduckgo_search`).
  3. **Concrete Changes**:
     * In `setup.sh`, add `pip install duckduckgo-search trafilatura`.
     * In `web_grounding.py:_fetch_search_results()`:
       ```python
       try:
           from duckduckgo_search import DDGS
           with DDGS() as ddgs:
               return list(ddgs.text(query, max_results=max_results))
       except Exception as e:
           logger.warning("DuckDuckGo search failed: %s", e)
       ```
     * Add fallback to local offline documentation indexing (`index_docs.py`).
  4. **Manual Verification**: Run `python3 bin/web_grounding.py "Python asyncio tutorial" --json`; verify valid search results with titles and URLs are returned in JSON.

---

### Issue #21: Ephemeral Tool Buffer Disk Growth & Missing Cleanup
* **Classification**: Storage Management / RAMDisk Bloat
* **Impact**: Medium
* **Discovered In**: `src/hermes_core/token_engine.py`
* **Symptom**: `/dev/shm` accumulated thousands of orphan `hermes_ephemeral_*.log` files.
* **Root Cause**: Logs created on every tool turn with zero FIFO pruning.
* **Precise Implementation Plan**:
  1. **Files to Touch**: `src/hermes_core/token_engine.py`.
  2. **Dependencies**: Standard Library `pathlib.Path`.
  3. **Concrete Changes**:
     * In `EphemeralToolBuffer.finalize()`:
       ```python
       existing_logs = sorted(RAMDISK.glob("hermes_ephemeral_*.log"), key=os.path.getmtime)
       if len(existing_logs) > 50:
           for old_log in existing_logs[:-50]:
               try: old_log.unlink()
               except OSError: pass
       ```
  4. **Manual Verification**: Create 60 dummy log files in `/dev/shm`; trigger `EphemeralToolBuffer.finalize()`; assert exactly 50 log files remain.

---

### Issue #22: Destructive Skill Promotion Folder Pruning Bug
* **Classification**: Skill Evolution / Data Loss Bug
* **Impact**: High
* **Discovered In**: `src/hermes_core/skill_evolution.py`
* **Symptom**: Rejection of a candidate skill ran `shutil.rmtree()` on active production skills directory.
* **Root Cause**: Candidate drafts were written directly into production directory before evaluation.
* **Precise Implementation Plan**:
  1. **Files to Touch**: `src/hermes_core/skill_evolution.py`.
  2. **Dependencies**: Standard Library `shutil`, `pathlib.Path`.
  3. **Concrete Changes**:
     * Define staging directory: `STAGING_DIR = Path.home() / ".hermes" / "staging_skills"`.
     * In `synthesize_candidate_skill()`, write candidate to `STAGING_DIR / skill_name / "SKILL.md"`.
     * In `evaluate_and_promote()`, only copy from `STAGING_DIR` to `primary_skills_dir` if `lift_report.certified == True`.
     * On rejection, delete only `STAGING_DIR / skill_name`.
  4. **Manual Verification**: Create existing skill `~/.hermes/skills/my_skill/SKILL.md`; run failed evolution cycle on `my_skill`; verify active `~/.hermes/skills/my_skill` remains untouched.

---

### Issue #23: Metacognitive Memory Ephemerality & RAMDisk State Loss
* **Classification**: Experience Store & Lifelong Learning
* **Impact**: High
* **Discovered In**: `src/hermes_core/experience_store.py`
* **Symptom**: Learned playbooks and negative constraints wiped on reboot.
* **Root Cause**: `ExperienceStore` defaulted to `/dev/shm/hermes_experience_store.json`.
* **Precise Implementation Plan**:
  1. **Files to Touch**: `src/hermes_core/experience_store.py`.
  2. **Dependencies**: Standard Library `pathlib.Path`, `sqlite3` or `json`.
  3. **Concrete Changes**:
     * Set persistent default: `DEFAULT_STORE = Path.home() / ".hermes" / "memory" / "experience_store.json"`.
     * Implement atomic file replacement (`tempfile.NamedTemporaryFile` + `os.replace`) to prevent corruption during power loss.
  4. **Manual Verification**: Record an episode; verify file exists at `~/.hermes/memory/experience_store.json`; verify data persists across sessions.

---

### Issue #24: OpenSkills Single-Level Scanner Drops Categorized Skills
* **Classification**: Skill Discovery & Architecture
* **Impact**: High
* **Discovered In**: `src/hermes_core/openskills_manager.py`
* **Symptom**: OpenSkills discovery reported 0 skills because skills are in subdirectories (`apple/`, `github/`).
* **Root Cause**: `_rebuild_index()` used flat `iterdir()` checking only 1 folder level.
* **Precise Implementation Plan**:
  1. **Files to Touch**: `src/hermes_core/openskills_manager.py`.
  2. **Dependencies**: Standard Library `pathlib.Path`.
  3. **Concrete Changes**:
     * In `_rebuild_index()`:
       ```python
       for skills_dir in self.skills_dirs:
           if not skills_dir.exists(): continue
           for skill_file in skills_dir.rglob("SKILL.md"):
               try:
                   pkg = self._parser.parse(skill_file)
                   self._skill_index[pkg.manifest.name] = pkg
               except Exception:
                   pass
       ```
  4. **Manual Verification**: Call `manager.discover_skills()`; assert all 62 categorized skills are discovered and listed.

---

### Issue #25: Lack of Base Skill Marketplace / Lead Developer Pack Pre-Bundling
* **Classification**: Environment Setup & Capability Gap
* **Impact**: High
* **Discovered In**: `executable_setup.sh`, `private_skills/`
* **Symptom**: Core developer skills had to be created ad-hoc rather than pre-seeded at setup.
* **Root Cause**: `setup.sh` lacked an upstream skill synchronization phase.
* **Precise Implementation Plan**:
  1. **Files to Touch**: `private_dot_hermes/bin/executable_setup.sh`, `private_skills/`.
  2. **Dependencies**: Git / GitHub `awesome-claude-skills`.
  3. **Concrete Changes**:
     * In `setup.sh`, add a skill synchronization step bundling standard categories:
       * `software-development/` (tdd, refactoring, code-review)
       * `devops/` (docker, github-actions, observer-gate)
       * `frontend/` (react, generative-ui, tailwind)
     * Register them in `chezmoi` so they are automatically deployed on `chezmoi apply`.
  4. **Manual Verification**: Run `setup.sh`; verify `~/.hermes/skills/` contains the full suite of categorized developer skills.

---

### Issue #26: Absence of Automatic Post-Generation Auto-Formatting & Linter Pipeline
* **Classification**: Code Quality & Pre-Commit Automation
* **Impact**: Medium
* **Discovered In**: `src/hermes_core/working_memory.py`, `src/hermes_core/tools.py`
* **Symptom**: Generated code had styling/PEP 8 errors; `FastASTPreCommitGate` falsely rejected code with `count("{") != count("}")`.
* **Root Cause**: No auto-formatter hook in `write_file()`; naive brace string counting.
* **Precise Implementation Plan**:
  1. **Files to Touch**: `src/hermes_core/working_memory.py`, `src/hermes_core/tools.py`.
  2. **Dependencies**: `ruff` (Astral), `prettier`, `tree-sitter`.
  3. **Concrete Changes**:
     * In `FastASTPreCommitGate.validate_code_syntax()`: replace brace count with Tree-sitter error node detection.
     * In `tools.py:write_file()`:
       * If `.py`: run `ruff format` and `ruff check --fix` on the content string in-memory before writing.
       * If `.js`/`.ts`/`.html`/`.css`: run `prettier --stdin-filepath` formatting.
  4. **Manual Verification**: Call `write_file("test.py", "def foo(  a,b ):\n x=1\n return x")`; verify written file is clean PEP 8 formatted (`def foo(a, b):\n    x = 1\n    return x`).

---

### Issue #27: CLI Flag Schema Discrepancy & Verbose Mode Ambiguity
* **Classification**: CLI Usability & Argument Parsing
* **Impact**: Medium
* **Discovered In**: `hermes` CLI entry point, `test_developer_workflows_e2e.py`
* **Symptom**: Passing `--verbose` / `-v` crashed with `unrecognized arguments: --verbose`.
* **Root Cause**: Top-level `argparse.ArgumentParser` did not register `--verbose`.
* **Precise Implementation Plan**:
  1. **Files to Touch**: `private_dot_hermes/src/hermes_core/cli.py`.
  2. **Dependencies**: Standard Library `argparse`, `logging`.
  3. **Concrete Changes**:
     * In top-level argument parser:
       ```python
       parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose debug logging")
       ```
     * In main entry point, if `args.verbose`: set `logging.basicConfig(level=logging.DEBUG)` and `os.environ["HERMES_DEBUG"] = "1"`.
  4. **Manual Verification**: Run `hermes -v --help` and `hermes -z "test" -v`; assert flag is accepted and debug output is printed.

---

### Issue #28: Agent & Benchmark Flag Amnesia & Missing Canonical Runner SDK
* **Classification**: Harness Usability & Invocation Invariant
* **Impact**: High
* **Discovered In**: `test_hermes_live_prompts.py`, `test_developer_workflows_e2e.py`
* **Symptom**: Tests and subagents omitted critical flags (`--in`, `--yolo`, `--skills`, `--accept-hooks`), causing hangs or wrong working directories.
* **Root Cause**: Lack of a typed Python SDK runner.
* **Precise Implementation Plan**:
  1. **Files to Touch**: `src/hermes_core/runner.py` (New File), `tests/roadmap6_adversarial/conftest.py`.
  2. **Dependencies**: Standard Library `subprocess`, `dataclasses`.
  3. **Concrete Changes**:
     * Create `src/hermes_core/runner.py` with `HermesRunner` class:
       ```python
       @dataclass
       class HermesRunResult:
           returncode: int
           stdout: str
           stderr: str
           duration_sec: float
           usage: Dict[str, Any]

       class HermesRunner:
           def __init__(self, cwd: Optional[Path] = None, skills: Optional[List[str]] = None, headless: bool = True):
               self.cwd = (cwd or Path.cwd()).resolve()
               self.skills = skills or []
               self.headless = headless

           def run(self, prompt: str) -> HermesRunResult:
               cmd = [shutil.which("hermes") or "hermes", "-z", prompt]
               if self.headless: cmd.extend(["--yolo", "--accept-hooks"])
               if self.skills: cmd.extend(["--skills", ",".join(self.skills)])
               cmd.extend(["--in", str(self.cwd)])
               # Execute with non-blocking I/O stream activity heartbeat
               rc, out, meta = run_with_group_teardown(cmd, cwd=str(self.cwd))
               return HermesRunResult(returncode=rc, stdout=out, stderr="", duration_sec=meta.get("elapsed", 0.0), usage={})
       ```
  4. **Manual Verification**: Import `HermesRunner` in a test script; run `runner.run("test")`; assert all required flags are automatically passed and working directory is strictly bound.

---

### Issue #29: Session Resumption Prefix-Cache Invalidation, Skill De-Activation, & Context Drift
* **Classification**: Session State & Token Engine Invariant
* **Impact**: High
* **Discovered In**: `session_persistence.py`, `prompt_slotting.py`, `context_compactor.py`
* **Symptom**: 
  1. When resuming a session via `hermes -c` or `hermes --resume <session_id>`, `llama-server` prefix cache reuse drops from 98% to 0%, forcing a full 25K+ token prompt reprocessing stall (10–15s latency on Turn 1).
  2. Previously loaded OpenSkills and active MCP tool servers are not re-hydrated into the resumed session, leaving the agent without the skills it acquired during earlier turns.
  3. Long sessions (30+ turns) re-inject bloated raw message transcripts on resume, pushing context close to the slot boundary instead of utilizing compact `<|ARCHITECTURAL_WORKING_MEMORY_ANCHOR|>` state summaries.
* **Root Cause**:
  1. Message history serialization on resume altered message order or dynamic timestamp headers in Turn 0, breaking deterministic prefix hashing in `llama-server`.
  2. `DurableSessionState` serialized task DAGs and file snapshots, but did not persist active `loaded_skills` manifests or active MCP server endpoints in `NodeReceipt`.
* **Precise Implementation Plan**:
  1. **Files to Touch**: `src/hermes_core/session_persistence.py`, `src/hermes_core/openskills_manager.py`, `src/hermes_core/prompt_slotting.py`.
  2. **Dependencies**: `google/adk-python` (Stateful session resumption), `mcp[cli]`.
  3. **Concrete Changes**:
     * In `DurableSessionState`: add `loaded_skill_names: List[str] = Field(default_factory=list)` and `active_mcp_servers: List[str] = Field(default_factory=list)`.
     * In `checkpoint()`: capture `openskills_manager.get_loaded_skill_names()` and persist them in `session_state.json`.
     * In `restore()`: automatically call `openskills_manager.load_skill(name)` for every persisted skill name upon session restore.
     * In `prompt_slotting.py:compile_resumed_context()`: enforce **Deterministic Prefix Slotted Layout**:
       * Slot 1 (Immutable Static Prefix): System prompt + Tool schemas (ensures 100% KV cache hit).
       * Slot 2 (Working Memory Anchor): `<|ARCHITECTURAL_WORKING_MEMORY_ANCHOR|>` + completed task receipts (<800 tokens).
       * Slot 3 (Recent Window): Only the last 2 conversation turns.
  4. **Manual Verification**: Run a 5-turn session loading a skill `hermes -s polars-data-analysis`; exit; resume with `hermes -c "continue previous task"`; verify `llama-server` slot log shows `cache reuse: >95%` and `polars-data-analysis` tools are immediately available on Turn 1.

---

### Issue #30: Unbounded Database & Cache Growth, Missing Auto-Pruning, & WAL Bloat
* **Classification**: Storage Management & Database Lifecycle Invariant
* **Impact**: High
* **Discovered In**: `src/hermes_core/symbol_graph.py`, `src/hermes_core/web_grounding.py`, `src/hermes_core/token_engine.py`
* **Symptom**:
  1. Ad-hoc JSON cache files (`web_grounding_cache.json`, `experiential.jsonl`) grow indefinitely without capacity bounds or TTL eviction, eventually consuming gigabytes of disk/RAMDisk.
  2. SQLite databases (`symbol_graph.db`) accumulate dead pages and bloated WAL files (`.db-wal`) that never shrink or truncate after large symbol deletions.
  3. No central database size manager exists to enforce global storage ceilings (e.g. max 500MB total agent footprint).
* **Root Cause**:
  1. Caches used custom dictionary dumps (`json.dump`) rather than an established disk cache manager with LRU/LFU eviction.
  2. SQLite connections lacked `PRAGMA auto_vacuum = INCREMENTAL`, `PRAGMA wal_checkpoint(TRUNCATE)`, and `PRAGMA incremental_vacuum` cleanup routines.
* **Precise Implementation Plan**:
  1. **Files to Touch**: `src/hermes_core/db_manager.py` (New File), `src/hermes_core/symbol_graph.py`, `src/hermes_core/web_grounding.py`, `src/hermes_core/openviking_vfs.py`.
  2. **Dependencies**: `diskcache` (`grantjenks/python-diskcache` PyPI), Standard Library `sqlite3`.
  3. **Concrete Changes**:
     * **DiskCache Migration for Transient Caching:**
       * Replace `web_grounding_cache.json` and speculative caches with `diskcache.Cache(directory=Path.home() / ".hermes/cache/web", size_limit=256*1024*1024, evict="lru")`.
       * Automatically evicts oldest entries when exceeding 256MB.
     * **Unified SQLite Lifecycle & Auto-Pruning PRAGMAs (`db_manager.py`):**
       * Create a standard database initializer for all SQLite databases (`symbol_graph.db`, `openviking_vfs.db`, `experience_store.db`):
         ```python
         def open_hardened_sqlite(db_path: Path) -> sqlite3.Connection:
             conn = sqlite3.connect(db_path, timeout=10.0)
             conn.execute("PRAGMA journal_mode = WAL;")
             conn.execute("PRAGMA synchronous = NORMAL;")
             conn.execute("PRAGMA auto_vacuum = INCREMENTAL;")
             conn.execute("PRAGMA wal_autocheckpoint = 1000;")
             return conn

         def vacuum_and_truncate_wal(conn: sqlite3.Connection):
             conn.execute("PRAGMA incremental_vacuum;")
             conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
         ```
       * Call `vacuum_and_truncate_wal(conn)` on session close / checkpoint to physically return freed disk space to the OS.
  4. **Manual Verification**: Populate 500MB of temporary cache entries into `diskcache`; verify cache automatically prunes and stays $\le 256\text{MB}$. Run a heavy re-indexing cycle in `SymbolGraph`; call `vacuum_and_truncate_wal()`; verify `.db-wal` size shrinks to 0 bytes.

---

### Issue #31: Universal Polyglot In-Flight Auto-Formatting Pipeline in `write_file()`
* **Classification**: Code Quality & Pre-Commit Automation
* **Impact**: High
* **Discovered In**: `src/hermes_core/tools.py`, `src/hermes_core/working_memory.py`
* **Symptom**: Code generated across languages (Python, JS/TS, Rust, Go, C++, HTML/CSS, Shell, Markdown) contains formatting defects, unaligned braces, missing imports, or style violations because formatters are not automatically invoked upon file generation.
* **Root Cause**: `write_file()` performed only AST parsing for Python and crude brace counting for JS without running native language formatters.
* **Precise Implementation Plan**:
  1. **Files to Touch**: `src/hermes_core/tools.py`, `src/hermes_core/formatter_pipeline.py` (New File), `executable_setup.sh`.
  2. **Dependencies**: `ruff` (Python), `biome` (JS/TS/JSON/CSS via `@biomejs/biome`), `rustfmt` (Rust), `gofmt` (Go), `clang-format` (C/C++), `shfmt` (Bash).
  3. **Concrete Changes**:
     * In `executable_setup.sh`, ensure `ruff`, `biome`, `shfmt`, and `clang-format` are pre-installed in container.
     * In `formatter_pipeline.py`:
       ```python
       def auto_format_and_lint_content(filepath: str, content: str) -> tuple[str, list[str]]:
           ext = Path(filepath).suffix.lower()
           # 1. Python: Astral Ruff (<5ms)
           if ext == ".py":
               return run_ruff_format_and_check(content)
           # 2. Web/JS/TS/JSON/CSS: Biome (<3ms)
           elif ext in {".js", ".ts", ".jsx", ".tsx", ".json", ".css"}:
               return run_biome_format(filepath, content)
           # 3. Rust: rustfmt
           elif ext == ".rs":
               return run_rustfmt(content)
           # 4. Go: gofmt
           elif ext == ".go":
               return run_gofmt(content)
           # 5. Shell: shfmt
           elif ext in {".sh", ".bash"}:
               return run_shfmt(content)
           return content, []
       ```
     * In `tools.py:write_file()`: pipe `content` through `auto_format_and_lint_content()` before writing to disk.
  4. **Manual Verification**: Call `write_file("app.tsx", "const   x:string='hello' ;")`; verify file written to disk is formatted cleanly by Biome as `const x: string = "hello";`.

---

### Issue #32: Tool Calling & JSON Schema Governance via Instructor & FastMCP
* **Classification**: Tool Calling & Schema Generation
* **Impact**: High
* **Discovered In**: `src/hermes_core/swarm_engine.py`, `src/hermes_core/codebase_memory_mcp.py`
* **Symptom**: Custom `function_to_schema()` lost field constraints, docstrings, and nested Pydantic types, causing SLMs to hallucinate invalid parameter formats.
* **Root Cause**: Ad-hoc inspection logic lacked Pydantic v2 JSON Schema generators and structured tool calling adapters.
* **Precise Implementation Plan**:
  1. **Files to Touch**: `src/hermes_core/swarm_engine.py`, `src/hermes_core/tools.py`.
  2. **Dependencies**: `instructor` (`jxnl/instructor` PyPI), `mcp[cli]` (Anthropic FastMCP), `pydantic` v2.
  3. **Concrete Changes**:
     * Refactor all Hermes tool signatures to use typed Pydantic models with `Field(description="...")`.
     * Replace ad-hoc `function_to_schema()` with Instructor / Pydantic v2's native schema generator:
       ```python
       import instructor
       from pydantic import TypeAdapter

       def pydantic_function_to_schema(model_cls: type[BaseModel]) -> Dict[str, Any]:
           schema = model_cls.model_json_schema()
           return {
               "type": "function",
               "function": {
                   "name": model_cls.__name__,
                   "description": model_cls.__doc__ or f"Execute {model_cls.__name__}",
                   "parameters": schema
               }
           }
       ```
     * Wire FastMCP server endpoints directly into Hermes tool registration.
  4. **Manual Verification**: Register a tool with `Literal["a", "b"]` and nested `Dict[str, int]`; generate schema; verify output contains full `enum: ["a", "b"]` and typed property definitions matching OpenAI / Anthropic tool-calling specs.
