# AGENTS.md — Phase 24 Autonomous Offline LoGRA/NoRA Weight Evolution Evaluation

> **Project**: Hermes Agent OS — Phase 24 Evaluation Harness  
> **Literature**: NVIDIA *LoGRA: Low-Rank Gradient Random Approximation* (arXiv:2610.06647), *NoRA: Normalized Rank Adaptation* (arXiv:2608.31036)  
> **Target Scenario**: `scenario/offline_adapter_engine.py` (Temporal Mutual Exclusion, VRAM Quorum Guard, LoGRA gradient sketches, NoRA Frobenius normalization ||A||_F == 1.0, MTP post-resume throughput >= 42.4 tok/s)  
> **Verification Gate**: `pytest tests/phase24_autonomous_logra_eval/ -q && python3 -c "import json; t=json.load(open('tests/phase24_autonomous_logra_eval/autonomous_logra_metrics.json')); r=json.load(open('/tmp/hermes_verified_receipt.json')); assert t['temporal_mutual_exclusion_verified'] is True and t['peak_total_vram_mib'] <= 4812.0 and t['nora_frobenius_norm'] == 1.0 and t['kl_divergence'] <= 0.05 and t['post_resume_mtp_tok_per_sec'] >= 42.4 and r['exitstatus'] == 0"`

---

## 1. Goal Contract Standard

```text
/goal Execute and verify Autonomous Offline LoGRA/NoRA Weight Evolution in scenario/offline_adapter_engine.py, asserting Temporal Mutual Exclusion (TME), VRAM quorum <= 650 MiB, peak VRAM <= 4812 MiB, rank-64 LoGRA gradient sketches, NoRA Frobenius normalization ||A||_F == 1.0, and post-resume MTP draft throughput >= 42.4 tok/s.

outcome:
  1. Inspect scenario/offline_adapter_engine.py and scenario/training_buffer/samples.jsonl.
  2. Verify VRAMQuorumGuard enforces temporal mutual exclusion and prevents VRAM over-allocation.
  3. Validate rank-64 LoGRA gradient sketching eliminating dense optimizer buffers.
  4. Assert NoRA down-projection Frobenius normalization ||A||_F == 1.0.
  5. Assert post-consolidation KL divergence <= 0.05.
  6. Assert post-resume Port 8138 MTP throughput >= 42.4 tok/s.
  7. All tests in . pass with exit code 0.

verify: pytest . -q
```

---

## 2. Invariant Rules
1. **Temporal Mutual Exclusion**: Training must never co-exist with Port 8138 inference. Quorum guard must ensure VRAM <= 650 MiB.
2. **Hardware Envelope**: Peak total VRAM must never exceed 4,812.0 MiB on the RTX 3050 Laptop GPU.
3. **NoRA Frobenius Norm**: Initialization of adapter down-projection matrix A must equal 1.0.
4. **Bounded Policy Drift**: KL divergence against base model must remain <= 0.05.
5. **Zero Bespoke Debt**: All code changes must remain self-contained within the testbed.
