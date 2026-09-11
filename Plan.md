# MASTER AGI TESTING & EVALUATION PLAN: AUTONOMOUS LOOPS & CAPABILITY STRESS-TESTING

**Version:** 3.1.0-AGI-EVAL  
**Target:** Hermes Agent OS (Era 10 / v3.0.0-AGY-FRONTIER)  
**Execution Vehicle:** Native Hermes CLI (`hermes "<prompt>"` / `/loop` / `hermes -z "<prompt>"`)  
**Objective:** Factually evaluate AGI capabilities, long-horizon autonomous loops, frontier harness performance, and self-learning mechanisms under natural, non-synthetic human prompts without hardcoded tool invocations.

---

## 1. Evaluation Philosophy: The Natural Autonomous Loop Standard

To prevent artificial or biased benchmark results, **zero prompts in this suite will dictate tool names or syntax** (e.g., no "call `view_file`" or "use `bwrap`"). Every prompt is expressed as an authentic, high-level user objective spanning software engineering, system architecture, data science, security analysis, and self-improvement.

### What Makes This an AGI / Frontier Harness Test?
1. **Autonomous Skill & Tool Discovery**: Hermes must independently analyze the intent, consult its registry of 26 plugins and 50+ skills, and select the appropriate tools without prompting.
2. **Autonomous Decomposition (Magentic-One Pattern)**: Hermes must establish a **Task Ledger** (roadmap, verified facts, milestones) and monitor a **Progress Ledger** turn-by-turn.
3. **Stall Circuit Breaking**: If an execution path hits a dead end, Hermes must catch the stall after 2 turns, reflect on the error trace, and mutate its strategy rather than thrashing.
4. **Surgical Precision (Claude Code SEARCH/REPLACE)**: Hermes must execute minimal, atomic diffs rather than file dumps, pre-verifying Python AST syntax before writing.
5. **Deterministic Process Reward Model (PRM)**: Diff size bounds (<= 80 lines) and Shannon entropy guards ($1.2 <= H <= 6.5$) must actively safeguard the context window.
6. **Rich Google AGY Deliverables**: When reporting complex findings, Hermes must spontaneously emit structured artifacts (GFM alerts, Mermaid diagrams, multi-slide carousels, HTML auxiliary preview pane apps).
7. **Empirical Verification & Rollback**: Every modification must be validated through automated test execution in the isolated sandbox, with instant git rollback on failure.
8. **Trajectory Observability**: Every single interaction must be logged to SQLite WAL (`trajectories.db`) with SWE-agent observation windowing (head/tail 25 lines).

---

## 2. Environment & System Readiness Verification

All required runtimes, system CLI utilities, and python data science packages have been provisioned in the `ws-hermes` container:
- **System Tools**: `git`, `curl`, `jq`, `rg` (ripgrep), `fd` (fd-find), `sqlite3`, `bwrap` (bubblewrap), `tree`.
- **Python Toolchain (v3.11.15 in venv)**: `pandas`, `numpy`, `scipy`, `polars`, `matplotlib`, `seaborn`, `sympy`, `duckdb`, `fastembed`, `fastmcp`, `ast-grep-py`, `ruff`, `playwright`, `trafilatura`, `pydantic`.
- **Active Plugins**: 26 native plugins active in `hermes-pack.yaml` and `.hermes/config.yaml`.
- **Contract Baseline**: 266 passed tests with 0 failures in 12.37s.

---

## 3. The 10 Frontier AGI Stress-Testing Batches

Each batch contains a natural human prompt, the underlying research capabilities being tested, and the concrete verification criteria.

---

### Batch 1: Full-Stack Algorithmic Engineering & Autonomous Loop
* **The Natural Prompt**:
  ```text
  hermes "I need a high-performance, concurrent LRU cache in Python with O(1) read/write access, TTL expiration per key, and thread safety. Write the implementation along with an exhaustive pytest test suite testing high-concurrency race conditions and TTL expiration edge cases. Run the tests in the sandbox, verify 100% pass rate, and document the architectural design."
  ```
* **Frontier Capabilities Evaluated**:
  - Autonomous Maker-Verifier decomposition (`@architect` contract $\to$ `@coder` implementation $\to$ `@tester` execution).
  - Code-as-Action in Bubblewrap (`bwrap`) sandbox.
  - AST syntax validation and Ruff polyglot formatting.
  - Zero-regression test verification.
* **Verification Criteria**:
  - Creates implementation file and test file in workspace.
  - Successfully executes `pytest` inside the sandbox with 0 errors.
  - Demonstrates thread safety and TTL expiration handling without deadlocks.

---

### Batch 2: System Architecture Analysis & Google AGY Generative UI Artifact
* **The Natural Prompt**:
  ```text
  hermes "Analyze our entire Hermes Agent OS plugin architecture under .hermes/plugins/. Identify every security boundary, execution coordinator, and memory store. Synthesize your findings into a comprehensive architectural report artifact containing:
  1. A GitHub [!IMPORTANT] alert explaining the physical 6GB VRAM and <= 4,800 MiB limits.
  2. A Mermaid diagram illustrating the flow of a user request through NeMo guardrails, Magentic-One ledgers, and the BPE workspace.
  3. A 4-backtick carousel comparing standard multi-turn JSON tool calling with smolagents Code-as-Action.
  4. A standalone single-file HTML dashboard with interactive Chart.js graphs displaying the distribution of the 26 plugins across functional domains."
  ```
* **Frontier Capabilities Evaluated**:
  - `antigravity_bridge` Artifacts Engine (`AGYArtifactsManager`).
  - GFM alert formatting (`[!IMPORTANT]`).
  - Mermaid diagram generation with parenthesis label sanitization.
  - Four-backtick multi-slide carousel syntax.
  - Standalone Generative UI HTML auxiliary app creation with bundled Chart.js.
* **Verification Criteria**:
  - Emits markdown artifact into `.gemini/antigravity-cli/brain/<conv-id>/` or `.hermes/artifacts/`.
  - Emits valid HTML dashboard loadable in any browser.
  - Manifest file updated in `artifacts_manifest.jsonl`.

---

### Batch 3: Long-Horizon Autonomous Refactoring & Surgical Diffing
* **The Natural Prompt**:
  ```text
  hermes "Inspect the codebase memory symbol indexer under .hermes/plugins/symbol_index/. Review how functions and classes are parsed. Formulate a refactoring plan to add docstring token length tracking to indexed functions. Apply the change using surgical SEARCH/REPLACE diffs without touching any unrelated lines, run our contract test suite to confirm zero regressions, and commit the verified improvement."
  ```
* **Frontier Capabilities Evaluated**:
  - Tree-sitter AST symbol extraction and inspection.
  - Claude Code byte-verbatim SEARCH/REPLACE diff engine.
  - Deterministic Code PRM diff size checking (<= 80 lines).
  - Zero-regression contract test execution (266 tests).
  - Automatic git pre-commit snapshotting.
* **Verification Criteria**:
  - Modifies only targeted lines in `symbol_index`.
  - All 266 contract tests pass without a single regression.
  - Clean git commit generated.

---

### Batch 4: Self-Referential Meta-Harness Audit & Trajectory Mining
* **The Natural Prompt**:
  ```text
  hermes "Inspect our execution history in the SQLite trajectories database. Group previous turns by exit code and tool usage, identify any recurring errors or high-latency operations, and formulate a formal Spec-Kit hypothesis in .hermes/evolution/hypotheses/ to optimize future tool execution. Run our verification gate to ensure the evolution engine is calibrated."
  ```
* **Frontier Capabilities Evaluated**:
  - SQLite WAL trajectory extraction from `trajectories.db`.
  - `self_evolution` Meta-Harness outer loop (`TraceFailureAnalyzer`).
  - Spec-Kit contract format hypothesis formulation (`H-XXX.json`).
  - Zero-regression test verification gate (`SpecVerificationGate`).
* **Verification Criteria**:
  - Queries `trajectories.db` directly without file corruption.
  - Creates a valid hypothesis JSON in `.hermes/evolution/hypotheses/`.
  - Verifies baseline score vs target score.

---

### Batch 5: Multi-Modal Data Science & Statistical Dashboard
* **The Natural Prompt**:
  ```text
  hermes "Generate a synthetic dataset of 1,000 API request logs containing timestamps, response latencies (log-normal distribution), status codes (200, 400, 500), and endpoint names using Pandas and NumPy. Compute key descriptive statistics (P50, P95, P99 latencies), detect anomalous latency spikes using IQR, and write a Python script that exports a clean summary report and saves a visualization."
  ```
* **Frontier Capabilities Evaluated**:
  - Autonomous usage of newly installed `pandas`, `numpy`, `matplotlib`, `scipy`.
  - Execution inside the unprivileged Bubblewrap sandbox.
  - Statistical anomaly detection and log-normal modeling.
  - File generation and validation.
* **Verification Criteria**:
  - Executes script cleanly using the venv python interpreter.
  - Calculates P50, P95, P99 accurately.
  - Emits data and visual output without memory leak.

---

### Batch 6: Security Boundary, Shannon Entropy & Constitutional Audit
* **The Natural Prompt**:
  ```text
  hermes "Perform a strict security and constitutional audit on our project environment. Scan the codebase for high-entropy strings, potential API keys, unmasked credentials, and dangerous shell execution patterns. Check the Shannon entropy of all detected tokens, verify against our Colang 2.0 NeMo guardrails, and emit an audit ledger report."
  ```
* **Frontier Capabilities Evaluated**:
  - `agentshield` Secret Scanner & Shannon entropy calculator.
  - `nemo_guardrails` Colang 2.0 input/output policy enforcement.
  - Cryptographic SHA-256 Merkle audit trail (`verification_evidence.db`).
  - Constitutional AI adherence (Principle of Least Privilege).
* **Verification Criteria**:
  - Accurately computes Shannon entropy $H$.
  - Rejects false positives while catching high-entropy patterns ($H > 4.6$).
  - Records verification evidence in SQLite.

---

### Batch 7: Cross-Framework Protocol & A2A Collaboration
* **The Natural Prompt**:
  ```text
  hermes "We need to integrate with Google's Agent2Agent (A2A) protocol. Verify that our agent card at /.well-known/agent-card.json is properly formatted according to the A2A v1 specification. Then, simulate an incoming JSON-RPC 2.0 message/send request to initiate a background code audit, verify that an isolated Git worktree is provisioned, and check the task status via tasks/get."
  ```
* **Frontier Capabilities Evaluated**:
  - `antigravity_bridge` A2A Protocol Server (`A2AAgentCardServer`).
  - Standard `agent-card.json` schema validation.
  - JSON-RPC 2.0 request parsing and lifecycle state transitions (`working` -> `completed`).
  - Google Jules isolated Git worktree worker provisioning (`JulesWorktreeSandbox`).
* **Verification Criteria**:
  - Emits compliant A2A agent card JSON.
  - Returns valid JSON-RPC 2.0 response with `taskId` and `status: "working"`.
  - Demonstrates worktree isolation without affecting `main` branch.

---

### Batch 8: Continuous Autonomous Loop (`/loop`) Problem Solving
* **The Natural Prompt**:
  ```text
  hermes "/loop We have an intermittent bug where large terminal command outputs cause context window bloat and attention drift. Investigate how SWE-agent observation windowing is implemented in plugins/trajectory_recorder/. Write a unit test that simulates a 200-line shell output, verify that the windowing function truncates it to 50 lines (keeping the first 25 and last 25 lines with a clear truncation message), and run the test until verified green."
  ```
* **Frontier Capabilities Evaluated**:
  - Long-horizon `/loop` iterative goal seeking.
  - SWE-agent observation windowing verification.
  - Magentic-One Progress Ledger monitoring and stall counter checks.
  - Dynamic test authoring and execution.
* **Verification Criteria**:
  - Continues loop autonomously until test is verified green.
  - Proves head/tail 25-line windowing invariant holds.
  - Terminates cleanly upon goal achievement.

---

### Batch 9: Dynamic Web Grounding & Frontier Research Synthesis
* **The Natural Prompt**:
  ```text
  hermes "Search the web for the latest 2026 developments regarding 'Meta-Harness arXiv:2603.28052' and 'Microsoft FrogNano 4B coding agent'. Synthesize the two approaches: compare Meta's outer-loop harness modification with Microsoft's [0.3, 0.7] learnability frontier RL training. Explain how a local 4B model on an RTX 3050 GPU can combine both techniques to achieve frontier-level coding performance without fine-tuning weights."
  ```
* **Frontier Capabilities Evaluated**:
  - Native web search / grounding toolset (`SearXNG` / `ddgs` / `trafilatura`).
  - High-level technical synthesis across competing frontier paradigms.
  - Hardware-grounded reasoning (RTX 3050, 6GB VRAM, zero-weight-tuning).
  - Progressive context structuring.
* **Verification Criteria**:
  - Retrieves authentic, accurate paper concepts.
  - Articulates the mathematical rationale of the $[0.3, 0.7]$ reward envelope.
  - Recommends concrete harness engineering patterns matching Hermes architecture.

---

### Batch 10: Complete System Integration & Disaster Recovery
* **The Natural Prompt**:
  ```text
  hermes "Demonstrate our disaster recovery and zero-regression guarantees. Introduce an intentional syntax or logic error into a temporary test file in .hermes/tests/contracts/. Run the contract test suite, demonstrate that our verification gate detects the failure, witness the automatic rollback mechanism restore the clean working state, and verify that all 266 tests are green again."
  ```
* **Frontier Capabilities Evaluated**:
  - Negative boundary testing & failure injection.
  - 2-Strike Tabu search branch swapper (`branch_swapper`).
  - Spec-Kit zero-regression verification gate (`SpecVerificationGate`).
  - Automated `git reset --hard` rollback to clean HEAD.
* **Verification Criteria**:
  - Intentionally introduced error is flagged immediately by test runner.
  - Automatic rollback restores workspace without user intervention.
  - Full suite returns to 266/266 green tests.

---

## 4. Execution Protocol & Verification Playbook

### Step 1: Execute a Prompt via Native Hermes CLI
Run the selected batch prompt directly from the terminal or inside the `ws-hermes` container:
```bash
# Example for Batch 1:
hermes "I need a high-performance, concurrent LRU cache in Python with O(1) read/write access, TTL expiration per key, and thread safety. Write the implementation along with an exhaustive pytest test suite testing high-concurrency race conditions and TTL expiration edge cases. Run the tests in the sandbox, verify 100% pass rate, and document the architectural design."
```

### Step 2: Observe Autonomous Behavior
Watch the live execution stream for:
1. **No Manual Tool Directives**: Does Hermes figure out which files to create, which tests to write, and when to run `pytest`?
2. **Dual Ledgers**: Does Hermes maintain task milestones and progress state?
3. **Sandbox Isolation**: Does Hermes execute code safely in `bwrap`?
4. **Trajectory Logging**: Check `trajectories.db`:
   ```bash
   sqlite3 ~/.hermes/cache/trajectories.db "SELECT id, role, tool_name, exit_code, constitutional_score FROM trajectories ORDER BY id DESC LIMIT 5;"
   ```

### Step 3: Verify Integrity & Sync
After executing the prompt batches, run the master exam to certify that zero regressions occurred:
```bash
make test
```
All 266 contract tests must remain 100% green.
