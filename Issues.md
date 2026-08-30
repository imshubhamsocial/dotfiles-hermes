# Issues & Architectural Fragility Audit (ws-hermes)

This document registers all operational bugs, loopholes, regressions, and architectural vulnerabilities discovered during the end-to-end audit, live adversarial evaluation, and exhaustive static inspection of every tool, script, plugin, and configuration across the Hermes agentic harness. It also provides an exhaustive physical audit of where the codebase relies on artificial timeouts, arbitrary token budgets, fixed context limits, hardcoded sleeps, and prompt-policed constraints rather than deterministic physical mechanisms.

---

## 1. Registered Subsystem, Tool, & Agentic Vulnerabilities

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
  * Implement a physical output token ceiling ($\le 600\text{ tokens}$ per turn) at the engine dispatch level.
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
  * In `cli.py`, auto-detect non-interactive TTY environments and automatically bind `--in` to `Path.cwd()` if not provided.

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
* **Remediation**:
  * **Eliminate Wall-Clock Timers:** Replace static timeouts with **I/O Stream Activity Heartbeats** (which only flag a deadlock if zero bytes are received on stdout/stderr for $>15\text{s}$).
  * **Enforce Turn Output Chunking:** Limit single-turn generation to $\le 600\text{ tokens}$ so each individual turn executes and yields in $\le 15\text{ seconds}$.
  * **State-Driven DAG Termination:** Signal task completion deterministically via invariant verification (tests pass + artifacts verified).

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

### Issue #14: Speculative Tool Executor Promise Abandonment & Memory Leak
* **Classification**: Async Tool Execution / Resource Leak
* **Impact**: Medium
* **Discovered In**: `src/hermes_core/speculative_executor.py`
* **Symptom**: Speculative tool promises taking $>5.0\text{s}$ are abandoned, marked as `REJECTED`, and re-executed synchronously. Furthermore, completed promises are never evicted from `self.promises`.
* **Root Cause**: Hardcoded timeout polling on futures and missing LRU eviction policy on `self.promises`.
* **Remediation**:
  * Use event-driven futures callbacks (`future.add_done_callback`) and bind `self.promises` using an LRU cache.

---

### Issue #15: Deterministic Code Extractor Monoglot Python Destruction
* **Classification**: Code Extraction & Tool Calling
* **Impact**: High
* **Discovered In**: `private_dot_hermes/bin/executable_extract_code_mode.py`
* **Symptom**: Extracting non-Python code blocks (Bash, HTML, CSS, JavaScript, SQL, JSON, YAML) from markdown fences fails with `"extract_code: fenced output contained no parsable code body"`.
* **Root Cause**: `extract_code()` filters candidate code chunks by passing them to `ast.parse(candidate)`. Any non-Python syntax raises `SyntaxError` and is discarded.
* **Remediation**:
  * Accept code blocks tagged with language markers (e.g. ```` ```bash ````, ```` ```html ````) and validate syntax using language-specific linters rather than assuming all code is Python.

---

### Issue #16: External Directory Expansion in Skill Verification
* **Classification**: Configuration & Environment Resilience
* **Impact**: Medium
* **Discovered In**: `private_dot_hermes/bin/executable_verify_skills_config.py`
* **Symptom**: Profiles declaring `external_dirs` with tildes or unexpanded shell variables fail pre-run verification if environment variables differ between host and container.
* **Root Cause**: Path existence checks relied on raw environment expansions without canonicalizing paths via `Path.resolve()`.
* **Remediation**:
  * Use normalized `os.path.expanduser(os.path.expandvars(p))` before validating directory existence.

---

### Issue #17: Inter-Bot Communication & Synergy Bus Memory Leak
* **Classification**: Multi-Bot & Reactive Bus / Memory Leak
* **Impact**: High
* **Discovered In**: `src/hermes_core/synergy_bus.py`
* **Symptom**: Long-running multi-agent sessions or continuous background tasks continuously consume RAMDisk and memory until exhaustion.
* **Root Cause**: `SynergyEventBus.event_history` appends every published event (`TASK_SPAWN`, `TOOL_CALL`, `VFS_MUTATION`) into an unbounded in-memory Python list without any eviction policy or ring buffer size limit.
* **Remediation**:
  * Replace unbounded list with `ThreadSafeRingBuffer(capacity=1000)` from `thread_safe_ringbuffer.py`.

---

### Issue #18: Multi-Bot Delegation Hardcoded Mock Orchestration
* **Classification**: Multi-Agent Orchestration / Mock Stub
* **Impact**: Critical
* **Discovered In**: `src/hermes_core/multi_bot_delegation.py`
* **Symptom**: `execute_delegation_pipeline()` does not actually execute multi-bot turns or generate code via LLM tools—it immediately returns pre-fabricated mock success strings (`"Architectural specification formulated in .hermes/plan.json..."`).
* **Root Cause**: The delegation orchestrator was authored as a prototype stub with synthetic return objects rather than connecting to the live Swarm / Hub dispatch loop.
* **Remediation**:
  * Wire `MultiBotOrchestrator` to invoke real agent turns via `HermesOrchestrator.run()` / `hub_cli.py` with actual tool dispatch and output verification.

---

### Issue #19: Swarm Engine Function Schema Type Coercion & Docstring Loss
* **Classification**: Tool Calling & Schema Generation
* **Impact**: Medium
* **Discovered In**: `src/hermes_core/swarm_engine.py`
* **Symptom**: Tools with complex type signatures (`Optional[int]`, `Union[str, Path]`, `Literal[...]`, Pydantic models) are exposed to the model as generic `"type": "string"` with uninformative `"description": "Parameter {name}"`.
* **Root Cause**: `function_to_schema()` uses a primitive `if/elif` type check and does not parse docstrings (Google/Sphinx/Numpydoc) for argument descriptions.
* **Remediation**:
  * Parse docstrings via `inspect.getdoc()` or `docstring_parser` to extract precise parameter semantics and generate full JSON Schema constraints (`enum`, `minimum`, `format`).

---

### Issue #20: Web Grounding Module Import Failure & Search Black Hole
* **Classification**: Web Grounding & External Knowledge
* **Impact**: Critical
* **Discovered In**: `src/hermes_core/web_grounding.py`
* **Symptom**: All web searches in `WebGroundingEngine` fail silently and return `[]` (empty results).
* **Root Cause**:
  1. Line 171 attempts `from ddgs import DDGS`, which does not exist in standard PyPI (standard library is `duckduckgo_search`).
  2. Neither `duckduckgo_search` nor a live `SEARXNG_URL` is configured by default, causing both primary and fallback search paths to fail.
* **Remediation**:
  * Fix import to `from duckduckgo_search import DDGS` and install `duckduckgo_search`.
  * Add automatic fallback to `executable_extract_web_content.py` and local offline documentation index (`index_docs.py`).

---

### Issue #21: Ephemeral Tool Buffer Disk Growth & Missing Cleanup
* **Classification**: Storage Management / RAMDisk Bloat
* **Impact**: Medium
* **Discovered In**: `src/hermes_core/token_engine.py`
* **Symptom**: `/dev/shm` fills up with thousands of orphan `hermes_ephemeral_*.log` files during heavy coding sessions.
* **Root Cause**: `EphemeralToolBuffer.finalize()` writes full subprocess stdout/stderr streams to `/dev/shm` on every single command turn, but never registers a FIFO capacity cap.
* **Remediation**:
  * Add a deterministic FIFO RingBuffer in `EphemeralToolBuffer` capping stored log count to 50 entries.

---

### Issue #22: Destructive Skill Promotion Folder Pruning Bug
* **Classification**: Skill Evolution / Data Loss Bug
* **Impact**: High
* **Discovered In**: `src/hermes_core/skill_evolution.py`
* **Symptom**: If an autonomous evolution cycle fails its A/B lift gate (+15% requirement), the engine deletes the entire skill directory, accidentally destroying existing production skills sharing the same name.
* **Root Cause**: `synthesize_candidate_skill()` writes candidate drafts directly to `~/.hermes/skills/{skill_name}/SKILL.md`. If A/B certification fails, `evaluate_and_promote()` calls `shutil.rmtree(candidate_file.parent)`, deleting the entire folder.
* **Remediation**:
  * Write candidate drafts to an isolated staging directory (e.g. `~/.hermes/staging_skills/`). Only copy to `~/.hermes/skills/` after the A/B lift gate is certified.

---

### Issue #23: Metacognitive Memory Ephemerality & RAMDisk State Loss
* **Classification**: Experience Store & Lifelong Learning
* **Impact**: High
* **Discovered In**: `src/hermes_core/experience_store.py`
* **Symptom**: All accumulated failure patterns, negative constraints, and positive playbooks are wiped on machine reboot or container restart.
* **Root Cause**: `ExperienceStore` defaults its database path to `/dev/shm/hermes_experience_store.json` (RAMDisk).
* **Remediation**:
  * Default storage to persistent disk at `~/.hermes/memory/experience_store.json` (or sync with `experiential.jsonl`), with optional RAMDisk write-through caching.

---

### Issue #24: OpenSkills Single-Level Scanner Drops Categorized Skills
* **Classification**: Skill Discovery & Architecture
* **Impact**: High
* **Discovered In**: `src/hermes_core/openskills_manager.py`
* **Symptom**: OpenSkills discovery returns 0 skills even when 62+ valid skills exist on disk.
* **Root Cause**: `_rebuild_index()` performs a flat 1-level `iterdir()` scan (`skills_dir / skill_dir / SKILL.md`). Because skills are organized in subdirectories (`creative/comfyui/SKILL.md`, `software-development/polars-data-analysis/SKILL.md`), all categorized skills are completely missed.
* **Remediation**:
  * Replace 1-level iteration with recursive globbing (`skills_dir.rglob("SKILL.md")`).

---

### Issue #25: Lack of Base Skill Marketplace / Lead Developer Pack Pre-Bundling
* **Classification**: Environment Setup & Capability Gap
* **Impact**: High
* **Discovered In**: `executable_setup.sh`, `private_skills/`
* **Symptom**: Common developer capabilities (e.g. Anthropic lead developer skills, official awesome-claude-skills, framework linters) must be manually coded or imported ad-hoc rather than pre-seeded at setup.
* **Root Cause**: `setup.sh` only deploys local static dotfiles and does not include an upstream skill package synchronizer.
* **Remediation**:
  * Add an upstream skill synchronization phase in `setup.sh` that bundles and categorizes core developer skills (TDD, Playwright, React, FastAPI, Git PR workflow) during initial setup.

---

### Issue #26: Absence of Automatic Post-Generation Auto-Formatting & Linter Pipeline
* **Classification**: Code Quality & Pre-Commit Automation
* **Impact**: Medium
* **Discovered In**: `src/hermes_core/working_memory.py`, `src/hermes_core/tools.py`
* **Symptom**: Code generated by the agent contains PEP 8 indentation errors, unformatted JSX/HTML, or trailing whitespace because formatters (`ruff format`, `black`, `prettier`) are never called automatically. Furthermore, `FastASTPreCommitGate` uses crude string counting (`count("{") != count("}")`) that falsely rejects valid code containing braces in strings.
* **Root Cause**: `write_file()` performs an AST syntax check but does not pipe code through standard formatters.
* **Remediation**:
  * Pipe synthesized code through `ruff format` / `prettier` automatically in `write_file()` and replace naive string counts with AST error node checks.

---

### Issue #27: CLI Flag Schema Discrepancy & Verbose Mode Ambiguity
* **Classification**: CLI Usability & Argument Parsing
* **Impact**: Medium
* **Discovered In**: `hermes` CLI entry point, `test_developer_workflows_e2e.py`
* **Symptom**: Passing standard debugging flags (e.g. `--verbose`, `-v`) to `hermes` crashes with `unrecognized arguments: --verbose`.
* **Root Cause**: Root CLI parser only registers specific subcommand arguments (or `--dev` tied strictly to `--tui`).
* **Remediation**:
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
* **Remediation**:
  * Implement a canonical, typed `HermesRunner` SDK module in `src/hermes_core/runner.py` that encapsulates all flags, I/O activity heartbeats, and working directory bindings.
  * In `cli.py`, auto-detect non-TTY environments (`not sys.stdin.isatty()`) and automatically bind `cwd` to current working directory if `--in` is omitted.

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
│ `src/hermes_core/synergy_bus.py`     │ Unbounded list append   │ Memory leak; events never purged│
├──────────────────────────────────────┼─────────────────────────┼─────────────────────────────────┤
│ `src/hermes_core/multi_bot_deleg...` │ Synthetic mock returns  │ Fakes architect/coder execution │
├──────────────────────────────────────┼─────────────────────────┼─────────────────────────────────┤
│ `src/hermes_core/swarm_engine.py`    │ Naive `function_to_sch..` Loss of param types & docstrings│
├──────────────────────────────────────┼─────────────────────────┼─────────────────────────────────┤
│ `src/hermes_core/web_grounding.py`   │ `from ddgs import DDGS` │ Broken import; searches return[]│
├──────────────────────────────────────┼─────────────────────────┼─────────────────────────────────┤
│ `src/hermes_core/token_engine.py`    │ Unreaped `/dev/shm` logs│ RAMDisk bloat on heavy runs     │
├──────────────────────────────────────┼─────────────────────────┼─────────────────────────────────┤
│ `src/hermes_core/skill_evolution.py` │ `shutil.rmtree` on fail │ Destroys pre-existing user skill│
├──────────────────────────────────────┼─────────────────────────┼─────────────────────────────────┤
│ `src/hermes_core/experience_store.py`│ `/dev/shm` default path │ State loss on system reboot     │
├──────────────────────────────────────┼─────────────────────────┼─────────────────────────────────┤
│ `src/hermes_core/openskills_manager` │ Flat 1-level `iterdir`  │ Misses all 62 categorized skills│
├──────────────────────────────────────┼─────────────────────────┼─────────────────────────────────┤
│ `src/hermes_core/working_memory.py`  │ `count("{")` naive gate │ False-positive syntax rejections│
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
│ `src/hermes_core/speculative_exec...`│ `timeout=5.0` hardcode  │ Promise abandonment; unbounded  │
│                                      │ unevicted promise dict  │ memory growth in long sessions  │
├──────────────────────────────────────┼─────────────────────────┼─────────────────────────────────┤
│ `bin/extract_code_mode.py`           │ `ast.parse` filter on   │ Destroys non-Python blocks      │
│                                      │ all fenced chunks       │ (Bash, HTML, JS, JSON, SQL)     │
├──────────────────────────────────────┼─────────────────────────┼─────────────────────────────────┤
│ `src/hermes_core/context_compactor.py`│ 4-tier token drop (95%) │ Heuristic token slicing drops   │
│                                      │ & message truncation    │ critical tool definitions       │
├──────────────────────────────────────┼─────────────────────────┼─────────────────────────────────┤
│ `src/hermes_core/process_guard.py`   │ Polling loops +         │ Requires explicit PGID kill     │
│                                      │ hardcoded 100ms grace   │ rather than arbitrary sleep     │
├──────────────────────────────────────┼─────────────────────────┼─────────────────────────────────┤
│ `executable_verify_harness_...py`    │ `timeout=5`, `timeout=90│ Brittle when under heavy CPU/   │
│                                      │ urllib `timeout=2`      │ GPU load during test runs       │
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
* **Where found:** `config.yaml` (`timeout: 180`, `inactivity_timeout: 120`), `container_cmd.py` (`timeout=10`), `observer_gate.py` (`timeout=5`, `timeout=3`), `speculative_executor.py` (`timeout=5.0`), test suites (`timeout=90`, `timeout=120`).
* **Why it is fragile:** Hardcoded seconds fail across heterogenous hardware. A linter or compiler taking 5.1 seconds on a busy machine triggers a hard failure.
* **Deterministic Fix:** Replace static wall-clock timers with **I/O Stream Activity Heartbeat Monitors** (which only flag deadlocks on zero data for $>15\text{s}$) and **State-Driven DAG Completion Signals**.

### B. Artificial Sleeps & Spin-Waits
* **Where found:** `comfyui/scripts/_common.py` (`time.sleep()`), `maps/scripts/maps_client.py` (`time.sleep(1.0)`), `grounded-citations/scripts/sources.py` (`time.sleep(0.05)`), `speculative_tool_executor.py` (`time.sleep(0.05)`).
* **Why it is fragile:** Sleeps inject artificial latency and introduce race conditions when background jobs complete sooner or later than the sleep window.
* **Deterministic Fix:**
  * Replace polling sleeps with **async event listeners** (e.g. WebSocket notifications for neural generation).
  * Replace sleep-based rate limiters with **Leaky Bucket / Token Bucket algorithms** that compute exact mathematical dispatch windows.

### C. Context Compression & Truncation Heuristics
* **Where found:** `context_compactor.py`, `conversation_loop.py`, `codebase_memory_mcp.py` (`truncate_to_tokens`).
* **Why it is fragile:** When context overflows, the compactor attempts a 95% token drop or truncates message history. If a prompt contains 22K tokens of system instructions and tool definitions, truncation heuristics fail to compress and cause the `"Cannot compress further"` error loop. In MCP, blind string slicing corrupts JSON syntax.
* **Deterministic Fix:**
  * **Dynamic Tool Offloading:** Never load all tool schemas simultaneously. Load only the tools permitted for the active subagent role via `capability_masks.py`.
  * **Structural AST Node Truncation:** Truncate data structures before JSON serialization.

### D. Prompt-Policed Guidelines vs. Physical Constraints
* **Where found:** `SOUL.md`, `AGENTS.md`, `dot_hermes_AGENTS.md`.
* **Why it is fragile:** Phrases like *"Never output massive blocks"*, *"Keep changes atomic"*, and *"Follow Phase 0"* rely entirely on the model's self-discipline. Small language models (4B–8B) routinely regress into completion mode when given ambiguous prompts.
* **Deterministic Fix:**
  * **Physical Token Brake:** Dispatcher truncates or interrupts single turns at $\le 600\text{ tokens}$ and demands tool execution.
  * **Pre-Execution Observer Gate:** File write operations greater than 150 lines without prior DAG blueprinting are structurally rejected by the tool executor.

---

## 4. Architectural Roadmap for Permanent Elimination

1. **Physical Turn Token Limiter**: Enforce `max_tokens: 600` per generation turn in `config.yaml` and `llama-server` dispatch to physically eliminate monolithic token dumping.
2. **I/O Stream Activity Heartbeat**: Replace all wall-clock timeouts with non-blocking stdout/stderr stream activity monitors.
3. **Schema-Driven DAG Enforcer**: Require `emit_plan_dag` tool call before `write_file` is unlocked.
4. **Structured Tree-Sitter MCP Slicing**: Truncate JSON AST elements structurally before serialization.
5. **Polyglot AST Symbol Graph**: Connect `tree_sitter_language_pack` to `symbol_graph.py` with `pathspec` gitignore resolution.
6. **Polyglot Markdown Code Extractor**: Remove Python-only AST filter from `extract_code_mode.py`.
7. **Recursive OpenSkills Discovery**: Update `openskills_manager.py` to recursively discover all categorized skills.
8. **Base Skill Pack Bundler**: Integrate upstream developer skill synchronization into `setup.sh`.
9. **Automated Linter/Formatter Gate**: Pipe generated files through `ruff format` / `prettier` automatically.
10. **Live Multi-Bot Orchestration**: Replace mock turn generators in `multi_bot_delegation.py` with real agent dispatch.
11. **Production Web Grounding**: Fix DuckDuckGo import, install `duckduckgo_search`, and link to offline doc search.
12. **Safe Skill Staging**: Stage candidate skills in `~/.hermes/staging_skills/` to prevent destructive deletion of active skills.
13. **Persistent Experience Store**: Migrate `/dev/shm/hermes_experience_store.json` to persistent disk at `~/.hermes/memory/`.
14. **Pre-Execution Policy Filter**: Intercept file writes and command executions in `capability_masks.py` before touching the OS.
