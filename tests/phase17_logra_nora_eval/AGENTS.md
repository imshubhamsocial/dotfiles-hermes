# AGENTS.md — Phase 17 Hardware-Bounded TTC Scaling & Hibernate-and-Train LoGRA/NoRA Evaluation

> **Project**: Hermes Agent OS — Phase 17 Evaluation Harness  
> **Literature**: NVIDIA LoGRA (arXiv:2610.06647), NoRA (arXiv:2608.31036), GrowMTP  
> **Target Scenario**: `scenario/` (LoGRA rank-64 random Gaussian gradient projection & Frobenius-normalized NoRA init)  
> **Verification Gate**: `pytest tests/phase17_logra_nora_eval/ -q && python3 -c "import json; t=json.load(open('tests/phase17_logra_nora_eval/training_telemetry.json')); assert t['peak_total_vram_mib'] <= 4812 and t['nora_frobenius_norm_init'] == 1.0 and t['kl_budget_respected'] is True and t['post_resume_mtp_tok_per_sec'] >= 39.7"`

---

## 1. Goal Contract Standard

```text
/goal Refactor LoGRAAligner.initialize_nora_down_proj in tests/phase17_logra_nora_eval/scenario/logra_aligner.py to enforce Frobenius normalization so that ||A||_F equals 1.0.

outcome:
  1. Inspect tests/phase17_logra_nora_eval/scenario/logra_aligner.py.
  2. Implement Frobenius normalization: A = A / frobenius_norm(A).
  3. Ensure ||A||_F equals 1.0 within numerical precision (error < 1e-6).
  4. All tests in tests/phase17_logra_nora_eval/scenario/test_logra_aligner.py pass with exit code 0.

verify: pytest tests/phase17_logra_nora_eval/scenario/test_logra_aligner.py -q
```
