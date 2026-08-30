# Issues & Architectural Fragility Audit (ws-hermes)

This document registers all operational bugs, loopholes, regressions, and architectural vulnerabilities discovered during the end-to-end audit and live adversarial evaluation of the Hermes agentic harness. It also provides an exhaustive physical audit of where the codebase relies on artificial timeouts, arbitrary token budgets, fixed context limits, hardcoded sleeps, and prompt-policed constraints rather than deterministic physical mechanisms.

---

## 1. Registered Adversarial Findings & Root Causes

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

## 2. Exhaustive Codebase Audit: Timeouts, Budgets, Sleeps & Fragile Heuristics

An in-depth physical inspection of the entire codebase revealed multiple locations where functionality is enforced via timeouts, sleeps, token caps, or prompt-policing instead of deterministic physical mechanisms.

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
│ `src/hermes_core/context_compactor.py`│ 4-tier token drop (95%) │ Heuristic token slicing can drop│
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
│ `SOUL.md` & `AGENTS.md`              │ Natural language rules  │ Prompt-policing can be ignored  │
│                                      │ for output conciseness  │ by SLMs without physical brakes │
└──────────────────────────────────────┴─────────────────────────┴─────────────────────────────────┘
```

---

## 3. Detailed Audit by Category

### A. Arbitrary Subprocess & Terminal Timeouts
* **Location**: `private_dot_hermes/config.yaml` (`timeout: 180`, `inactivity_timeout: 120`), `private_dot_hermes/bin/executable_container_cmd.py` (`timeout=10`), `private_dot_hermes/bin/executable_observer_gate.py` (`timeout=5`, `timeout=3`).
* **Why it is fragile**: Hardcoded seconds fail across heterogenous hardware (e.g. fast RTX 3050 vs slow CPU emulation). If a test runner or linter takes 5.1 seconds, the harness terminates it with an error.
* **Deterministic Replacement**: Use **I/O Heartbeat Monitors** (process output stream activity) and **Exit Status Events** rather than static wall-clock timers.

### B. Artificial Sleeps & Spin-Waits
* **Location**: `private_dot_hermes/private_skills/creative/comfyui/scripts/_common.py` (`time.sleep(delay)`), `private_dot_hermes/private_skills/productivity/maps/scripts/maps_client.py` (`time.sleep(NOMINATIM_RATE_LIMIT)`), `private_skills/research/grounded-citations/scripts/sources.py` (`time.sleep(0.05)`).
* **Why it is fragile**: Sleeps introduce artificial latency and can cause race conditions when background jobs complete sooner or later than the sleep window.
* **Deterministic Replacement**:
  * Replace polling sleeps with **async event listeners** (e.g. WebSocket notifications for ComfyUI).
  * Replace sleep-based rate limiters with **Leaky Bucket / Token Bucket algorithms** that compute exact mathematical wait times.

### C. Context Compression & Truncation Heuristics
* **Location**: `src/hermes_core/context_compactor.py`, `hermes-agent/agent/conversation_loop.py`.
* **Why it is fragile**: When context overflows, the compactor attempts a 95% token drop or truncates message history. If a prompt contains 22K tokens of system instructions and tool definitions, truncation heuristics fail to compress and cause the `"Cannot compress further"` error loop.
* **Deterministic Replacement**:
  * **Dynamic Tool Offloading**: Never load all tool schemas simultaneously. Load only the tools permitted for the active subagent role via `capability_masks.py`.
  * **Summary Anchoring**: Replace linear truncation with structural SQLite memory graphs (`experiential.jsonl`).

### D. Prompt-Policed Guidelines vs. Physical Constraints
* **Location**: `SOUL.md`, `AGENTS.md`, `dot_hermes_AGENTS.md`.
* **Why it is fragile**: Phrases like *"Never output massive blocks"*, *"Keep changes atomic"*, and *"Follow Phase 0"* rely entirely on the model's self-discipline. Small language models (4B–8B) routinely regress into completion mode when given ambiguous prompts.
* **Deterministic Replacement**:
  * **Physical Token Brake**: Dispatcher truncates or interrupts single turns at $\le 800\text{ tokens}$ and demands tool execution.
  * **Pre-Execution Observer Gate**: File write operations greater than 150 lines without prior DAG blueprinting are structurally rejected by the tool executor.

---

## 4. Architectural Roadmap for Permanent Elimination

1. **Physical Turn Token Limiter**: Enforce `max_tokens: 800` per generation turn in `config.yaml` and `llama-server` dispatch.
2. **Schema-Driven DAG Enforcer**: Require `emit_plan_dag` tool call before `write_file` is unlocked.
3. **Heartbeat-Based Process Supervisor**: Replace static `timeout=N` in `observer_gate.py` with process output stream activity tracking.
4. **Token Bucket Rate Limiting**: Replace all `time.sleep()` calls in skill scripts with exact token bucket timers.
5. **Pre-Execution Policy Filter**: Intercept file writes and command executions in `capability_masks.py` before touching the OS.
