# Phase 27: Two-Stage Zero-Eviction Decision Router — Implementation Checklist

> **Phase Directory**: `phase_27_two_stage_zero_eviction_decision_router`  
> **Status**: Completed Stage `02_impl` execution  

---

## 1. Targeted Symbols & Code Modules
- Target File(s): `tests/phase27_decision_router_eval/scenario/rate_limiter.py`
- Target Symbol: `TokenBucketRateLimiter.allow_request`
- Module Stems: `rate_limiter`
- Required Skills: `karpathy-surgical-diff`, `viking-retrieval`

---

## 2. Surgical Implementation Plan
- [x] Step 1: Formulate single-cause causal hypothesis:
  - **Hypothesis**: In `TokenBucketRateLimiter.allow_request`, updating `self.last_refill = now` only when `tokens >= cost` causes `last_refill` to remain stale across rejected requests during dry spells. When time elapses, this permits an unauthorized accumulated burst. Unconditionally updating `self.last_refill = now` ensures continuous monotonic refill dynamics.
- [x] Step 2: Ensure non-git backup exists (`<target>.hermes.bak`) if mutating Domain B files (Domain C repo: git tracked).
- [x] Step 3: Apply mutation via `jev_mutate_module` adhering to Karpathy U12 15-line diff limit.
- [x] Step 4: Verify pre-commit `ast.parse` and post-write `ruff check` pass with code 0.
- [x] Step 5: Advance stage to `03_verify` in `03_verify/status.json`.
