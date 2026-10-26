# AGENTS.md — Phase 16 DreamRSI Offline Replay Simulator, MASS Role-Switched Meta-Loop & RRSI Stability Gate

> **Project**: Hermes Agent OS — Phase 16 Evaluation Harness  
> **Literature**: Dream-RSI (Google/DeepMind, arXiv:2609.14858), MASS (Sakana AI, arXiv:2610.12176), RRSI (Google, arXiv:2609.24972)  
> **Target Scenario**: `scenario/` (Dream replay engine counterfactual tree simulation and branch pruning)  
> **Verification Gate**: `pytest tests/phase16_dream_rsi_eval/ -q && python3 -c "import json; d=json.load(open('tests/phase16_dream_rsi_eval/dream_replay_results.json')); assert d['simulated_calls_reduction_ratio'] >= 1.40 and d['harness2_worktree_compose_gain'] > 0.0 and d['rrsi_stability_margin_exceeded'] is True and d['held_out_pytest_exit_code'] == 0"`

---

## 1. Goal Contract Standard

```text
/goal Refactor DreamReplayEngine.simulate_counterfactual_pruning in scenario/dream_engine.py to correct the branch pruning calculation and disk cache persistence.

outcome:
  1. Inspect scenario/dream_engine.py and diagnose the branch pruning and caching bug.
  2. Ensure counterfactual branch search prunes dead-end sequences when two consecutive failures occur (Two-Strike rule).
  3. Ensure replay tree states are cached to .hermes/cache/dream_worlds/<task_hash>.json.
  4. All tests in scenario/test_dream_engine.py pass with exit code 0.

verify: pytest scenario/test_dream_engine.py -q
```
