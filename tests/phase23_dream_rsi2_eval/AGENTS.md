# AGENTS.md — Phase 23 Dream-RSI 2.0 Replay Simulator Pool Evaluation

> **Project**: Hermes Agent OS — Phase 23 Evaluation Harness  
> **Literature**: Google DeepMind / UMD *Dream-RSI: Recursive Self-Improvement through Evolving Worlds* (arXiv:2609.14858), Google RRSI (arXiv:2609.24972)  
> **Target Scenario**: `scenario/replay_simulator.py` (Persistent replay trees, Doubly Robust value estimation, RRSI stability gate, >= 2.0x call reduction)  
> **Verification Gate**: `pytest tests/phase23_dream_rsi2_eval/ -q && python3 -c "import json; d=json.load(open('tests/phase23_dream_rsi2_eval/dream_rsi2_metrics.json')); r=json.load(open('/tmp/hermes_verified_receipt.json')); assert d['cuda_vram_delta_mib'] == 0 and d['call_reduction_ratio'] >= 2.0 and d['rrsi_stability_gate_passed'] is True and d['dream_eval_latency_ms'] <= 50.0 and r['exitstatus'] == 0"`

---

## 1. Goal Contract Standard

```text
/goal Verify and execute the Dream-RSI 2.0 Replay Simulator Pool in tests/phase23_dream_rsi2_eval/scenario/replay_simulator.py, asserting content-addressed replay tree persistence, Doubly Robust off-policy value estimation, RRSI variance stability gating (Delta >= k * sigma_0), and call reduction ratio >= 2.0x.

outcome:
  1. Inspect tests/phase23_dream_rsi2_eval/scenario/replay_simulator.py.
  2. Persist execution trajectories into content-addressed JSON replay trees.
  3. Execute Doubly Robust counterfactual policy evaluation on CPU RAM (latency <= 50.0 ms).
  4. Validate RRSI stability gate compliance rejecting high-variance spurious mutations.
  5. Assert call reduction ratio >= 2.0x and 0 MiB CUDA VRAM delta.
  6. All tests in tests/phase23_dream_rsi2_eval/ pass with exit code 0.

verify: pytest tests/phase23_dream_rsi2_eval/ -q
```
