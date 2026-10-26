# Workspace Routing & ICM Execution Protocol (AGENTS.md)

> **Architectural Standard**: Jake Van Clief's Interpretable Context Methodology (ICM / MWP, arXiv:2603.16021)  
> **Layering Rule**: **60% Infrastructure** (POSIX/Git) | **30% Orchestration** (ICM Folders + FastMCP Pydantic v2) | **10% AI Cognition** (Gemma-4-E4B on Port 8138)  
> **Operational Scope**: You operate strictly on the active phase directory defined in `phases/status_ledger.json`.  
> **Context Discipline**: Never read `docs/reference/` or future `phases/phase_XX/` directories unless explicitly instructed. Maintain working context between 2,000 and 8,000 tokens.

---

## Stage Gate Machine (Mandatory Order)

### 1. RECON & INTENT (Stage `01_spec`)
- **Deliberation Tag**: Emit `<deliberation><global>...</global></deliberation>`.
- **Turn 1 Mandatory Dispatch**: Call `jev_compile_intent` and `extract_workspace_ast` on Turn 1 before mutating files.
- **Context Scope**: Read **ONLY** `phases/<active_phase>/01_spec/spec.md` and `phases/<active_phase>/03_verify/status.json`.
- **Stage Progression**: Write concrete symbol targets and causal hypotheses into `02_impl/task.md`. Update `status.json` stage to `"02_impl"`.

### 2. SURGICAL IMPLEMENTATION (Stage `02_impl`)
- **Deliberation Tag**: Emit `<deliberation><focus id="target_symbol">...</focus></deliberation>`.
- **Context Scope**: Read `02_impl/task.md`. If domain-specific rules are needed, call `skill_view(name)` on demand.
- **Shadow Backups**: If mutating non-Git files (Domain B), verify `<target>.hermes.bak` exists first.
- **Karpathy U12 Limit**: Apply ONE causal change per turn via `jev_mutate_module` (<= 15 lines diff). Never use raw `sed`/`awk` or modify test assertions.
- **Pre-Commit Linter Gate**: If `jev_mutate_module` returns AST or `ruff` errors, fix them before advancing. Update `status.json` stage to `"03_verify"`.

### 3. DETERMINISTIC VERIFICATION & FAILURE HANDLING (Stage `03_verify`)
- **Deliberation Tag**: Emit `<deliberation><local>...</local></deliberation>`.
- **Execution Command**: Execute the exact command in `phases/<active_phase>/03_verify/contract.sh`.

#### HAPPY PATH (Exit Code 0)
- Verify `/tmp/hermes_verified_receipt.json` exists with `"exitstatus": 0` and `query_live_nvml_vram()` reports `used_mib <= 5400.0`.
- Update `03_verify/status.json` to `{"stage": "complete", "strikes": 0, "verified": true}`.
- Advance `phases/status_ledger.json` to the next phase.

#### UNHAPPY PATH — STRIKE 1 (Exit Code != 0, `strikes == 0`)
- Increment `strikes` to `1` in `03_verify/status.json`.
- Read **ONLY** the 40/60 head-tail truncated traceback (bottom 600 bytes).
- Formulate a single new causal hypothesis in `02_impl/task.md` and return to Stage `02_impl`.

#### UNHAPPY PATH — STRIKE 2 TABU ROLLBACK (Exit Code != 0, `strikes >= 1`)
- **HALT** incremental patching immediately.
- Execute `git checkout HEAD -- <file>` (or restore `<file>.hermes.bak` from `.hermes/cache/shadow_backups/`).
- Call `jev_anneal_cluster` with the failure trace to write a clean-slate spec in `01_spec/specs/annealed_<id>.md`.
- Reset `strikes` to `0`, and restart from Stage `01_spec`.

#### UNHAPPY PATH — INFRASTRUCTURE / VRAM BREACH
- If `used_mib > 5400.0`, upstream `.hermes/hermes-agent` is dirty (`git status --porcelain != ""`), or a required sidecar port (8138, 1933) is unreachable, abort immediately without mutating files and report the exact gate failure.

---

## Single-Stage Agent Execution Command

```bash
distrobox enter ws-hermes -- hermes chat --yolo -q '
Execute the next unverified phase in phases/status_ledger.json following ~/.hermes/SOUL.md and AGENTS.md:
1. Turn 1: Invoke jev_compile_intent and extract_workspace_ast.
2. Read phases/<active_phase>/03_verify/status.json and phases/<active_phase>/01_spec/spec.md. Do not read any other phase folders.
3. Document your surgical plan in 02_impl/task.md, apply mutations strictly via jev_mutate_module, and run 03_verify/contract.sh.
4. Enforce the Two-Strike Tabu rule on test failures: revert to clean state on Strike 2 and invoke jev_anneal_cluster.
5. Do not declare completion until 03_verify/contract.sh exits 0, /tmp/hermes_verified_receipt.json is sealed, and query_live_nvml_vram() confirms used_mib <= 5400.0.
'
```
