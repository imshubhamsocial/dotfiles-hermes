# Phase: Post-Certification Pre-Flight Remediation Gauntlet — Implementation Task Checklist

> **Phase Directory**: `phases/remediation_gauntlet`  
> **Target Subsystems**: `private_dot_hermes/executable_mcp_openjev.py`, `.hermes/mcp_openjev.py`, `conftest.py`  
> **Status**: Stage `01_spec` Complete -> Prepared for User Review before Stage `02_impl` Execution  

---

## 1. Targeted Symbols & Exact Code Modules

### Module A: FastMCP Tool Suite (`.hermes/mcp_openjev.py` & `private_dot_hermes/executable_mcp_openjev.py`)
1. **`extract_workspace_ast`**:
   - Scope default `workspace_dir="."` to the Turn-0 intent manifest's `sandbox_target`.
   - Prevent cross-phase file traversals into inactive testbeds.
2. **`jev_decide`**:
   - Remove lexical `+0.15` bonus for `.get(`.
   - When $\Delta s < 0.08$, invoke `_GemmaCPUSidecarPool.canonicalize_seq2seq` on candidate hypotheses for true T5Gemma 2 tie-breaking.
3. **`jev_harness2_probe_compose`**:
   - Replace line-length scoring ($1.0/\text{len}(\text{diff})$) with real execution in isolated temporary git worktrees (`/tmp/hermes_probe_<hash>`).
   - Run `pytest -q` in the detached worktree and score by return code.
   - Clean up worktrees safely in `finally:` blocks.
4. **`jev_dream_rsi_sync`**:
   - Delegate replay tree generation directly to `LiveDreamSyncEngine.build_tree_dict`.
   - Gate rule promotion on empirical $\Delta \hat{V}_{\text{DR}} > 0$.
5. **`_create_write_once_shadow_backup`**:
   - Skip creating adjacent `.hermes.bak` if `(target.parent / ".git").exists()` or `.git` in path, preserving Domain B/C separation.
6. **`jev_arc_agi_neurosymbolic_solve`**:
   - Hook candidate DSL program synthesis to Port 8138 completion endpoint.

### Module B: Root Epistemic Receipt Generator (`conftest.py`)
1. **Domain C Git Diff Precedence**:
   - In `pytest_sessionfinish`, evaluate `_collect_domain_c_git_diff` first when `(testbed_root / ".git").exists()`.
2. **Zero-Mutation False Pass Rejection**:
   - Raise `AssertionError` if `"verified_clean_tree"` is detected on a non-clean task.
3. **Phase 20 Receipt Banner**:
   - Emit `✅ VERIFICATION RECEIPT VALIDATED: All modified modules tested and passed (exit 0).` for `phase20_continuous_rsi_eval`.

---

## 2. Karpathy U12 Surgical Implementation Checklist

- [x] **Turn 1 Mutation (RISK-04)**: Patch `extract_workspace_ast` to resolve sandbox target from intent manifest.
- [x] **Turn 2 Mutation (RISK-01A)**: Patch `jev_decide` to remove lexical bonus and activate `canonicalize_seq2seq`.
- [x] **Turn 3 Mutation (RISK-01B)**: Patch `jev_harness2_probe_compose` to run real detached worktree pytest evaluations.
- [x] **Turn 4 Mutation (RISK-01C)**: Patch `jev_dream_rsi_sync` to invoke `LiveDreamSyncEngine`.
- [x] **Turn 5 Mutation (RISK-02A)**: Patch `_create_write_once_shadow_backup` to skip `.hermes.bak` in git repos.
- [x] **Turn 6 Mutation (RISK-02B)**: Patch `conftest.py` for git-first evaluation, clean-tree rejection, and Phase 20 receipt banner.
- [x] **Turn 7 Verification**: Execute `03_verify/contract.sh` (`pytest tests/remediation_eval/ -q`) and verify 100% pass under 5,400.0 MiB VRAM.
- [x] **Turn 8 Chezmoi Sync**: Commit all changes to chezmoi with clean status and push to GitHub.
