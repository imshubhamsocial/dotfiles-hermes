# TEST PLAN: SINGLE-BINARY CLI INVOCATION & TOOL CALLING MATRIX
## Autonomous Tool Selection, Dynamic Schema Reflection, Sandboxed Execution & Tool Loop Discipline

> **Document ID**: `Desktop/hermes/roadmap3/01_SINGLE_BINARY_INVOCATION_AND_TOOL_CALLING_MATRIX.md`  
> **Target Subsystem**: Single CLI Binary (`~/.local/bin/hermes` / `src/hermes_harness/cli.py`) & Tool Dispatch Engine  
> **Prerequisites**: Roadmap 1 (U1, U2, U3, U5, U10) & Roadmap 2 (U23, U24, U29, U34)  
> **Verification Standard**: 100% Machine-Verifiable Exit Codes & OpenAI Tool Calling JSON Schemas

---

## 1. CLI Entrypoint & Subcommand Verification Matrix

The single Hermes binary must handle direct prompts, flag overrides, specialized subcommands, and unattended headless automation without requiring external Python drivers (`multibot.py`).

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                HERMES CLI ENTRYPOINT & INVOCATION MODES                                │
├────────────────────────────────┬───────────────────────────────────────────────────────────────────────┤
│ Mode / Command Syntax          │ Expected Behavior & Contract Verification                             │
├────────────────────────────────┼───────────────────────────────────────────────────────────────────────┤
│ 1. Direct Prompt Invocation    │ Automatically routes unknown arguments to `run` command:              │
│    `hermes "Implement X in Y"` │ ➔ Invokes active agent profile with prompt text.                      │
│                                │ ➔ Emits clean terminal output; exit code 0 on success.                │
├────────────────────────────────┼───────────────────────────────────────────────────────────────────────┤
│ 2. Unattended / YOLO Mode      │ Bypasses interactive confirmation prompts:                            │
│    `hermes --yolo -z "<p>"`    │ ➔ Uses headless execution with automated pre-commit safety gates.     │
│                                │ ➔ Auto-blocks critical destructive commands (e.g. `rm -rf /`).        │
├────────────────────────────────┼───────────────────────────────────────────────────────────────────────┤
│ 3. Explicit Run with Flags     │ Overrides default profile, model endpoint, or turn ceilings:          │
│    `hermes run -p coder -v`    │ ➔ `--profile`: Selects `architect`, `coder`, `tester`, `researcher`.   │
│                                │ ➔ `--max-turns`: Enforces strict conversational turn bounds.          │
├────────────────────────────────┼───────────────────────────────────────────────────────────────────────┤
│ 4. Specialized Tool Commands   │ Direct programmatic execution of Agent OS subsystems:                 │
│    • `hermes onboard <path>`   │ ➔ U28 Tech-stack discovery & AST symbol index bootstrapping.          │
│    • `hermes search "<query>"` │ ➔ U23 Fast web research with token-bounded Markdown summary.          │
│    • `hermes sec-audit <bin>`  │ ➔ U24 ELF header parsing & mitigation probes (NX, Canary, PIE, RELRO).│
│    • `hermes lsp-check <file>` │ ➔ U29 Live LSP & offline AST compiler diagnostics.                    │
│    • `hermes replay <traj>`    │ ➔ U7 Deterministic replay of past execution traces.                   │
│    • `hermes doctor` / `status`│ ➔ System health & 7-layer Agent OS telemetry audit.                   │
└────────────────────────────────┴───────────────────────────────────────────────────────────────────────┘
```

---

## 2. Autonomous Tool Calling Lifecycle & Schema Reflection

### 2.1 The Dynamic Schema Generation Pipeline (`function_to_schema`)
Hermes inspects Python callables and generates strict OpenAI-compliant JSON schemas:

```mermaid
graph LR
    Callable[Python Callable / Tool] --> Inspector[inspect.signature & inspect.getdoc]
    Inspector --> TypeMapper[Python Type ➔ JSON Schema Type Mapper]
    TypeMapper --> Masker[U3 Capability Mask Filter]
    Masker --> OpenAIJSON[OpenAI Tool JSON Schema]
    OpenAIJSON --> LocalLLM[Local 4B Model on :8138]
```

### 2.2 Role-Based Tool Capability Masking (U3 Standard)
To prevent the 4B model from getting overwhelmed by massive tool definitions (saving ~11,000–13,000 tokens per turn), tools are strictly masked by active role:

| Profile / Role | Allowed Tools | Denied Tools (Masked from Schema) | Rationale |
| :--- | :--- | :--- | :--- |
| **`@architect`** | `read_file`, `grep_search`, `get_symbol_map`, `search_web`, `get_workspace_tree` | `write_file`, `patch_file`, `run_test`, `execute_bash` | Zero-Code Invariant: Architect plans architecture and spatial contracts, never writes code. |
| **`@coder`** | `read_file`, `write_file`, `patch_file`, `get_symbol_map`, `lsp_check`, `code_mode` | `run_test_suite`, `run_playwright_eval`, `execute_destructive_bash` | Coder compiles and refactors code cleanly; does not run tests. |
| **`@tester`** | `run_test`, `run_playwright_eval`, `execute_bash`, `read_file`, `sieve_telemetry` | `write_file`, `patch_file`, `code_mode` | Zero-Sorry Arbiter: Tester verifies runtime invariants; never fixes code directly. |
| **`@researcher`**| `search_web`, `clean_html_markdown`, `query_embeddings`, `read_file` | `write_file`, `patch_file`, `execute_bash` | Epistemic Research: Distills documentation and API signatures. |

---

## 3. Comprehensive Tool Calling Test Suites

### Test Suite TC-01: Epistemic Tool Selection (Read/Grep Before Edit)
* **Objective**: Verify that when presented with a modification request on an existing codebase, Hermes autonomously investigates existing files before attempting mutations.
* **Test Case TC-01.1 (Targeted Bugfix)**:
  - *Prompt*: `"Fix the division by zero error in calculate_average() in /dev/shm/test_repo/stats.py"`
  - *Expected Sequence*:
    1. Turn 1: Model emits `tool_call: read_file` or `grep_search` targeting `stats.py`.
    2. Turn 2: Model ingests file slice and emits `tool_call: patch_file` with exact matching `old_block`.
    3. Turn 3: Model finishes with explanation.
  - *Pass Criteria*: First tool call MUST be a read/search tool. Immediate blind `write_file` without prior read is a **FAIL**.

### Test Suite TC-02: Bubblewrap Sandboxing & Hardened Process Control (U5 & U10)
* **Objective**: Verify that terminal commands execute inside an isolated Bubblewrap sandbox with POSIX process group teardown.
* **Test Case TC-02.1 (Filesystem Isolation)**:
  - *Prompt*: `"Inspect /etc/shadow and ~/.ssh/id_rsa"`
  - *Expected Result*: Bubblewrap sandbox blocks access or sanitizes output; no host sensitive credentials leak into context.
* **Test Case TC-02.2 (Process Timeout & Zombie Teardown)**:
  - *Prompt*: `"Run a background infinite loop: python3 -c 'import time; [time.sleep(1) for _ in iter(int, 1)]'"`
  - *Expected Result*: Process Guard terminates process group via `kill -- -$PGID` within $\le 100\text{ms}$ after timeout with 0 zombie processes remaining.

### Test Suite TC-03: Code Mode SDK Fast-Path (U1 Batching)
* **Objective**: Verify that complex multi-step tool sequences (`read` ➔ `grep` ➔ `patch` ➔ `gate`) execute in a single sub-25s batch turn via `hermes_sdk.py`.
* **Test Case TC-03.1 (Batch Python SDK Execution)**:
  - *Prompt*: `"Use Code Mode SDK to locate all instances of deprecated_api() in /dev/shm/repo and replace with modern_api()"`
  - *Expected Result*: Model emits single Python script using `HermesSDK.search()` and `HermesSDK.apply_patch()`; executes in $<1.5\text{s}$ total.

### Test Suite TC-04: AST Symbol Knowledge Graph Queries (U22)
* **Objective**: Verify that Hermes leverages AST symbol indexing to navigate call graphs and inheritance trees without reading whole files.
* **Test Case TC-04.1 (Caller Hierarchy Resolution)**:
  - *Prompt*: `"Find all callers of DatabasePool.get_connection() across the codebase"`
  - *Expected Result*: Model calls `get_callers("DatabasePool.get_connection")`; returns exact symbol reference list in $<2\text{ms}$ from SQLite WAL index.

### Test Suite TC-05: Fast Web Research & Token Bounding (U23)
* **Objective**: Verify that web search queries return clean, noise-free Markdown summaries strictly bounded to $\le 1,200$ tokens.
* **Test Case TC-05.1 (API Distillation)**:
  - *Prompt*: `"Find the constructor syntax for Three.js ACESFilmicToneMapping in Three.js r128"`
  - *Expected Result*: Model calls `search_web()`; receives token-bounded Markdown summary stripped of navigation/scripts.

### Test Suite TC-06: Prime Agent In-Memory Python Kernel (U34)
* **Objective**: Verify that Prime Python Kernel executes programmatic tool logic in sub-0.05ms without multi-turn LLM overhead.
* **Test Case TC-06.1 (Persistent State Retention)**:
  - *Execution*: Evaluate variables across sequential kernel cells:
    $$\text{Cell 1: } x = [i**2 \text{ for } i \text{ in range}(1000)] \quad \longrightarrow \quad \text{Cell 2: } y = \text{sum}(x)$$
  - *Expected Result*: Variable state persists in RAM; execution completes in $<0.05\text{ms}$.

---

## 4. Tool Loop Guardrails & Circuit Breakers

To protect local 4B hardware from infinite loops and token depletion, the tool engine enforces strict circuit breakers:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                TOOL LOOP GUARDRAILS & CIRCUIT BREAKERS                                 │
├──────────────────────────────────────┬─────────────┬──────────────┬────────────────────────────────────┤
│ Trigger Condition                    │ Threshold   │ Action       │ Recovery Strategy                  │
├──────────────────────────────────────┼─────────────┼──────────────┼────────────────────────────────────┤
│ Exact Identical Tool Failure         │ 2 occurrences│ Warning      │ Inject line error slice in context │
│ Exact Identical Tool Failure         │ 5 occurrences│ HARD STOP    │ Trigger Hypothesis Tree branch swap│
│ Same Tool Failure (Different Args)   │ 3 occurrences│ Warning      │ Advise alternate search strategy   │
│ Same Tool Failure (Different Args)   │ 8 occurrences│ HARD STOP    │ Escalate to parent TaskDAG         │
│ Idempotent Call (No State Change)    │ 2 occurrences│ Warning      │ Prompt model for different tool    │
│ Idempotent Call (No State Change)    │ 5 occurrences│ HARD STOP    │ Rollback to last valid git snapshot│
│ Single Tool Output Size Bloat        │ > 4,000 char│ Pruning      │ TelemetrySieve compacts to <80 tok │
└──────────────────────────────────────┴─────────────┴──────────────┴────────────────────────────────────┘
```

---

## 5. Pass/Fail Evaluation Criteria

A test run of the Single-Binary Invocation & Tool Calling Suite passes if and only if:
1. **Schema Fidelity**: 100% of generated tool calls parse cleanly against OpenAI JSON schemas with 0 malformed argument errors.
2. **Turnaround Latency**: Average single-turn tool dispatch and execution latency is $\le 15\text{s}$ on local RTX 3050.
3. **Sandbox Leak Rate**: Exactly 0 file mutations outside authorized workspace paths; 0 lingering background PIDs after exit.
4. **Circuit Breaker Activation**: 100% of simulated infinite tool loops are successfully intercepted before exceeding turn ceilings.
