# Phase: Post-Certification Pre-Flight Remediation Gauntlet (RISK-01 to RISK-04) — Specification Manifest

> **Phase ID**: `remediation_gauntlet`  
> **Source Directives**:  
> - [`Hermes Agent OS Peer Review.md`](file:///var/home/imshubhamsocial/Desktop/GDR/GDR18/Output/Hermes%20Agent%20OS%20Peer%20Review.md) (GDR18 Peer Review)  
> - [`Now read this file, See what exactly Jake meant for GDR18 Remediations.md`](file:///var/home/imshubhamsocial/Desktop/GDR/GDR18/Output/Now%20read%20this%20file,%20See%20what%20exactly%20Jake%20meant%20for%20GDR18%20Remediations.md) (ICM Operational Guide)  
> **Architectural Standard**: Jake Van Clief's Interpretable Context Methodology (*ICM / MWP, arXiv:2603.16021*)  
> **Layering Rule**: **60% Infrastructure** (POSIX/Git/conftest) | **30% Orchestration** (FastMCP Pydantic v2) | **10% AI Cognition** (Gemma-4-E4B $\le 15$ lines)  
> **Hardware Boundary Assertion**: Discrete RTX 3050 Laptop GPU $\le 5,400.0\text{ MiB}$ Pure-GPU Ceiling; CPU Sidecars $0.0\text{ MiB}$ CUDA delta.

---

## 1. Executive Remediation Directives

Even though all 32 developmental phases are certified with 117/117 unit tests passing across 19 testbeds in 39.99s, four latent implementation discrepancies must be resolved before unattended evaluation on open-world benchmarks (SWE-bench, ARC-AGI-1/2, GAIA, Tau-bench):

| Risk ID & Severity | Subsystem / File | Discovered Defect | Formal Remediation Invariant |
| :--- | :--- | :--- | :--- |
| **RISK-01 (HIGH)** | `private_dot_hermes/executable_mcp_openjev.py` | `jev_harness2_probe_compose` scored patches by line length ($1.0/\text{len}(\text{diff})$) instead of running tests in git worktrees; `jev_decide` injected hardcoded `+0.15` bonus for `.get(` and skipped T5Gemma 2; `jev_dream_rsi_sync` wrote static `0.2353` DR gain; `jev_arc_agi_neurosymbolic_solve` used static templates. | Wire `git worktree add --detach /tmp/hermes_probe_<hash>` and score by `pytest -q` returncode; remove lexical bonus in `jev_decide` and call `_GemmaCPUSidecarPool.canonicalize_seq2seq` when $\Delta s < 0.08$; delegate `jev_dream_rsi_sync` to `LiveDreamSyncEngine.build_tree_dict`; dispatch candidate DSL programs via Port 8138 synthesizer. |
| **RISK-02 (MEDIUM-HIGH)** | `conftest.py` & `_create_write_once_shadow_backup` | Unconditional `.hermes.bak` creation in Git testbeds caused `conftest.py` to evaluate Domain B shadow backup on Run 1 and Domain C git diff on Run 2; zero-mutation runs sealed `"verified_clean_tree"`; Phase 20 omitted receipt assertion banner. | In `_create_write_once_shadow_backup`, skip creating `.hermes.bak` if `(target.parent / ".git").exists()`; in `conftest.py`, evaluate Domain C git diff first when `.git` exists; assert `modified != ["verified_clean_tree"]` on bug fixes; emit receipt banner in Phase 20. |
| **RISK-03 (MEDIUM)** | Port 8138 Slot 0 Concurrency | Background `hermes-rsi-daemon.service` cron ticks can interleave with foreground benchmark agents on Port 8138 Slot 0, evicting the non-pinned KV prefix beyond token 4,096. | Enforce Temporal Mutual Exclusion (TME): `systemctl --user stop hermes-rsi-daemon.service` during benchmark runs to guarantee 100% Slot 0 KV cache residency for the foreground agent. |
| **RISK-04 (LOW)** | `extract_workspace_ast` | Calling `extract_workspace_ast(workspace_dir=".")` scans parent workspace root, leaking cross-phase `.py` symbol names into SWA context. | Default `workspace_dir` in `extract_workspace_ast` to the active Turn-0 `sandbox_target` extracted from `.hermes/cache/intent_manifests/*.json`. |

---

## 2. Invariant Mathematical Equations & Physics

### A. SWA Attention Denominator Inflation Defense
$$\alpha_{i,j} = \frac{\exp\left(\frac{q_i k_j^\top}{\sqrt{d_k}}\right)}{\sum_{l \in \text{SWA}(i)} \exp\left(\frac{q_i k_l^\top}{\sqrt{d_k}}\right) + \sum_{m \in \text{History}} \exp\left(\frac{q_i k_m^\top}{\sqrt{d_k}}\right) + \sum_{n \in \text{Code}} \exp\left(\frac{q_i k_n^\top}{\sqrt{d_k}}\right)}$$
By scoping `extract_workspace_ast` strictly to `sandbox_target`, the code token denominator $\sum_{n \in \text{Code}} \exp(\cdot)$ is constrained to only the local taskbed symbols, preventing attention collapse on target AST symbols.

### B. Sequential Worktree Probing Verification
$$\text{Score}(P) = \mathbb{I}\left[\text{pytest}(W_P) == 0\right] \in \{0.0, 1.0\}$$
where $W_P = \text{git worktree add --detach } /tmp/hermes\_probe\_\text{hash}$. Winner is selected strictly on empirical verification, not line-length heuristics.

### C. Doubly Robust Counterfactual Off-Policy Evaluation
$$\hat{V}_{\text{DR}}(\pi_{\text{new}}) = \frac{1}{N} \sum_{i=1}^N \left[ \hat{Q}(s_i, \pi_{\text{new}}(s_i)) + \frac{\mathbb{I}[\pi_{\text{new}}(s_i) = a_i]}{p_{\text{old}}(a_i \mid s_i)} \left( R_i - \hat{Q}(s_i, a_i) \right) \right]$$
Gated by the RRSI lower-confidence bound: $\Delta \hat{V}_{\text{DR}} - 1.96 \cdot \text{SE} > 0$.

---

## 3. Operational Invariants for Active Stage
1. **Sub-8K Context Discipline**: Read ONLY this file during Stage `01_spec`.
2. **Turn 1 Reconnaissance**: Emit `<deliberation><global>...</global></deliberation>`, call `jev_compile_intent` and `extract_workspace_ast`.
3. **Task Formulation**: Populate `02_impl/task.md` with target files, line ranges, and checklists before advancing to Stage `02_impl`.
