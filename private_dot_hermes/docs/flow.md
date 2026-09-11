# End-to-End Component Flow & Execution Architecture (Era 10)

This document maps out how every subsystem interacts during a turn, and provides a clear guide for diagnosing what is working, what is failing, or where execution stalls.

---

## 1. End-to-End Execution Pipeline

```
[ User Prompt / Autonomous Task / A2A Request ]
                      │
                      ▼
 1. PREFLIGHT & HIERARCHICAL CONTEXT DISCOVERY
    ├── Hierarchical Rule Walker: Scans Layer 0 (Global) -> Layer 1 (Root AGENTS.md) -> Layer 2 (Scoped)
    ├── Progressive Disclosure: Compresses active rules to ≤ 400 tokens
    └── NVIDIA NeMo Pre-Execution Rail: Blocks destructive shell commands (; && rm -rf sudo)
                      │
                      ▼
 2. STRATEGIC PLANNING & DUAL LEDGERS (Magentic-One)
    ├── Task Ledger: High-level roadmap, verified facts, milestone checklist
    ├── Progress Ledger: Turn-by-turn operational monitor and sub-agent observations
    └── 2-Turn Stall Circuit Breaker: Intercepts loops if 2 consecutive turns yield zero progress
                      │
                      ▼
 3. ANTHROPIC TRINITY ROLE DECOMPOSITION & EXECUTION
    ├── @architect: Explores codebase via AST indexer; writes contract specifications
    ├── @coder: Synthesizes minimal diffs via Claude Code SEARCH/REPLACE blocks
    └── smolagents Code-as-Action: Executes raw Python scripts in Bubblewrap (bwrap) sandbox
                      │
                      ▼
 4. VERIFICATION GATES & PROCESS REWARD MODEL (PRM)
    ├── Deterministic AST PRM: Evaluates Python syntax, verifies diff format, enforces ≤ 80 lines
    ├── Shannon Entropy Monitor: Blocks low-entropy bloat (H < 1.2) & obfuscation (H > 6.5)
    ├── Zero-Regression Test Gate: Runs targeted test suite in sandbox
    └── Quorum Audit Gate: Author != Auditor consensus check (Fitness ≥ 0.85)
                      │
                      ├──► [TEST FAIL] ──► 2-Strike Tabu Swapper ──► Auto-Rollback (git reset) ──► Re-plan
                      │
                      ▼ [VERIFIED PASS]
 5. ARTIFACT EMISSION & TRAJECTORY PERSISTENCE
    ├── Google AGY Artifacts Engine: Emits GFM alerts, Mermaid graphs, carousels, or HTML aux apps
    ├── Gemini Thought Signatures: Preserves latent reasoning tokens across tool turns
    ├── SWE-agent Observation Windowing: Truncates terminal outputs keeping head/tail 25 lines
    ├── Trajectory Recorder: Appends full step history to SQLite WAL store (trajectories.db)
    └── BPE Workspace: Updates belief.md and progress.md for cross-session continuity
                      │
                      ▼
 6. META-HARNESS OUTER-LOOP SELF-EVOLUTION (Background / Idle)
    ├── Trace Failure Clustering: Analyzes failure patterns in trajectories.db
    ├── Spec Hypothesis Formulation: Generates targeted harness improvement hypothesis
    └── Candidate Evaluation: Runs 266 contract tests; commits only on 100% green zero-regression
```

---

## 2. Debugging Cheatsheet: What to Check When Something Fails

| Symptom | Probable Cause | Where to Look / Diagnostic Command |
|---|---|---|
| **GPU OOM / Process Killed** | Context tokens exceeded physical 6GB limit | Enforce hardware ceiling: `hermes doctor`<br>Ensure VRAM $\le 4,800$ MiB. |
| **Tool Execution Stalls / Loops** | 2-Turn Stall Circuit Breaker | Inspect Magentic-One Progress Ledger stall counter:<br>`hermes ledger status` |
| **Output Truncation / Context Rot** | Tool emitted massive log output | Handled automatically by SWE-agent observation windowing (keeps first 25 and last 25 lines). |
| **Gemini Tool Call Rejected (HTTP 400)** | Missing `thought_signature` | Verify `thought_signature.py` is loaded and decorating follow-up turns. |
| **Changes Refuse to Commit** | PRM or Quorum rejected code | Inspect AST syntax error or diff line count ($>80$ lines). Run `pytest .hermes/tests/contracts/`. |
| **Plugin Not Discovered** | Manifest missing or disabled | Verify entry in `hermes-pack.yaml` and run:<br>`hermes plugins list` |
| **Database Lock / Busy Errors** | SQLite not in WAL mode | Verify WAL mode: `sqlite3 ~/.hermes/cache/trajectories.db "PRAGMA journal_mode;"` |
