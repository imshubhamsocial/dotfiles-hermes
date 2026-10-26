# Phase 07: Native Closed-Loop RSI Skill Distillation — Implementation Checklist

> **Phase Directory**: `phase_07_native_closed_loop_rsi_skill_distillation`  
> **Status**: Stage `02_impl` execution complete  

---

## 1. Targeted Symbols & Code Modules
- Target File(s):
  - `tests/phase16_dream_rsi_eval/scenario/dream_engine.py`: persist tree state in `DreamReplayEngine.simulate_counterfactual_pruning`
  - `tests/phase16_dream_rsi_eval/benchmark_dream_rsi.py`: execute benchmark to generate `dream_replay_results.json`
- Module Stems:
  - `DreamReplayEngine.simulate_counterfactual_pruning`
- Required Skills:
  - `karpathy-surgical-diff`

---

## 2. Causal Hypotheses
1. In `DreamReplayEngine.simulate_counterfactual_pruning`, the counterfactual tree state `tree_dict` was computed in memory but omitted persisting to `self.cache_dir / f"{task_hash}.json"`. Persisting the replay tree to disk restores cache integrity.
2. Executing `benchmark_dream_rsi.py` validates DreamRSI replay reduction (2.000 >= 1.40), MASS 3-pass worktree gain (+23.53% > 0.0%), and RRSI stability margin, sealing `dream_replay_results.json`.

---

## 3. Surgical Implementation Plan
- [x] Step 1: Formulate single-cause causal hypothesis.
- [x] Step 2: Ensure non-git backup exists (`<target>.hermes.bak`) if mutating Domain B files.
- [x] Step 3: Apply mutation via `jev_mutate_module` adhering to Karpathy U12 15-line diff limit.
- [x] Step 4: Verify pre-commit `ast.parse` and post-write `ruff check` pass with code 0.
- [x] Step 5: Advance stage to `03_verify` in `03_verify/status.json`.
