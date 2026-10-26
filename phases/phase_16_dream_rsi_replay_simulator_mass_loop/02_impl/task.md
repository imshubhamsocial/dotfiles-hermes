# Phase 16: Dream-RSI Replay Simulator & MASS Loop — Implementation Checklist

> **Phase Directory**: `phase_16_dream_rsi_replay_simulator_mass_loop`  
> **Status**: Stage `02_impl` execution  

---

## 1. Targeted Symbols & Code Modules
- **Target File**: `tests/phase16_dream_rsi_eval/scenario/dream_engine.py`
- **Target Symbol**: `DreamReplayEngine.simulate_counterfactual_pruning`
- **Causal Hypothesis**: `DreamReplayEngine.simulate_counterfactual_pruning` computes `tree_dict` and `reduction_ratio` but fails to persist the simulated counterfactual branch to the content-addressed disk cache at `self.cache_dir / f"{task_hash}.json"`. Adding atomic JSON disk persistence restores disk cache availability, satisfying `test_disk_cache_persistence` and `test_dream_engine_caches_to_disk`.
- **Karpathy U12 Limit**: Single causal mutation <= 15 lines diff.

---

## 2. Surgical Implementation Plan
- [x] Step 1: Formulate single-cause causal hypothesis for `DreamReplayEngine.simulate_counterfactual_pruning`.
- [ ] Step 2: Ensure shadow backup (`<target>.hermes.bak`) exists.
- [ ] Step 3: Apply mutation via `jev_mutate_module` adhering to Karpathy U12 diff limit (<= 15 lines).
- [ ] Step 4: Verify pre-commit `ast.parse` and post-write `ruff check` pass with code 0.
- [ ] Step 5: Advance stage to `03_verify` in `03_verify/status.json`.
