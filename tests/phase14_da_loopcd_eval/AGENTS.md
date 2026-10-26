# AGENTS.md — Phase 14 Declarative Attention & LoopCD Testbed Orientation

> **Project**: Hermes Agent OS — Phase 14 Evaluation Harness  
> **Literature**: Declarative Attention (KAIST / Google DeepMind, arXiv:2609.02737), Apple LoopCD (arXiv:2610.02185)  
> **Target Scenario**: `scenario/uncertainty_branch/` (Token bucket rate limiter accumulation bug)  
> **Verification Gate**: `pytest tests/phase14_da_loopcd_eval/test_verify.py -q && python3 -c "import json; m=json.load(open('tests/phase14_da_loopcd_eval/metrics.json')); assert m['attended_token_reduction_pct'] >= 48.0 and m['loopcd_pass_at_1_gain'] > 0.0 and m['phase14_certified'] is True"`

---

## 1. Goal Contract Standard

```text
/goal Refactor TokenBucketRateLimiter.allow_request in scenario/uncertainty_branch/rate_limiter.py to resolve the token accumulation bug under rejected polling, structuring reasoning via Declarative Attention and LoopCD discrimination.

outcome:
  1. Inspect scenario/uncertainty_branch/rate_limiter.py.
  2. Frame analysis in thought using Declarative Attention tags: <global>, <focus id="TokenBucketRateLimiter.allow_request">, <local>.
  3. Discriminate hypotheses using LoopCD logprob scoring (jev_decide) or contrastive analysis.
  4. Apply surgical patch ensuring last_refill is updated unconditionally upon refill.
  5. All tests in scenario/uncertainty_branch/test_rate_limiter.py pass with exit code 0.

verify: pytest scenario/uncertainty_branch/test_rate_limiter.py -q
```
