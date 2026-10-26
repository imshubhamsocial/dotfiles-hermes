# Phase 09: OpenJev FastMCP Decision Gate — Implementation Checklist

> **Phase Directory**: `phase_09_openjev_fastmcp_decision_gate`  
> **Status**: Stage `02_impl` execution complete  

---

## 1. Targeted Symbols & Code Modules
- Target File(s):
  - `tests/phase27_decision_router_eval/scenario/rate_limiter.py`: `TokenBucketRateLimiter.allow_request`
  - `.hermes/mcp_openjev.py`: `jev_latent_deliberate` vector premise handling & `lipschitz_bound` metric
- Module Stems:
  - `TokenBucketRateLimiter.allow_request`, `jev_latent_deliberate`
- Required Skills:
  - `karpathy-surgical-diff`

---

## 2. Causal Hypotheses
1. In `TokenBucketRateLimiter.allow_request`, `self.last_refill` was only updated on successful requests. During repeated rejected polls, `last_refill` remained stale, permitting unauthorized sudden bursts. Setting `self.last_refill = now` on every call fixes the staleness defect.
2. In `jev_latent_deliberate`, accepting direct vector premise inputs and returning `lipschitz_bound` enables contractive fixed-point deliberation on CPU RAM with 0.0 MiB CUDA delta.

---

## 3. Surgical Implementation Plan
- [x] Step 1: Formulate single-cause causal hypothesis.
- [x] Step 2: Ensure non-git backup exists (`<target>.hermes.bak`) if mutating Domain B files.
- [x] Step 3: Apply mutation via `jev_mutate_module` adhering to Karpathy U12 15-line diff limit.
- [x] Step 4: Verify pre-commit `ast.parse` and post-write `ruff check` pass with code 0.
- [x] Step 5: Advance stage to `03_verify` in `03_verify/status.json`.
