# Phase 14: Declarative Attention & LoopCD Scoping — Implementation Checklist

> **Phase Directory**: `phase_14_declarative_attention_loopcd_scoping`  
> **Status**: Stage `02_impl` execution  

---

## 1. Targeted Symbols & Code Modules
- **Target File**: `tests/phase14_da_loopcd_eval/scenario/uncertainty_branch/rate_limiter.py`
- **Target Symbol**: `TokenBucketRateLimiter.allow_request`
- **Causal Hypothesis**: `TokenBucketRateLimiter.allow_request` only updates `self.last_refill = now` when `self.tokens >= cost`. Under rejected polls, `self.last_refill` remains stale, allowing elapsed time accumulation and burst tokens beyond capacity. Moving `self.last_refill = now` immediately after token replenishment ensures `last_refill` advances monotonically on every poll.
- **Karpathy U12 Limit**: Single causal mutation <= 15 lines diff.

---

## 2. Surgical Implementation Plan
- [x] Step 1: Formulate single-cause causal hypothesis for `TokenBucketRateLimiter.allow_request`.
- [ ] Step 2: Ensure shadow backup (`<target>.hermes.bak`) exists.
- [ ] Step 3: Apply mutation via `jev_mutate_module` adhering to Karpathy U12 diff limit (<= 15 lines).
- [ ] Step 4: Verify pre-commit `ast.parse` and post-write `ruff check` pass with code 0.
- [ ] Step 5: Advance stage to `03_verify` in `03_verify/status.json`.
