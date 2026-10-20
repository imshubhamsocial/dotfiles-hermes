# Invariant Rule: Phase 27 Selective Decision Routing and Uncertainty Gating

> **Scope**: Layer 4 Invariant Rule (Phase 27)  
> **Authority**: Princeton Inference Scaling fLaws (arXiv:2411.17501) & Apple LoopCD (arXiv:2610.02185)  
> **Hardware Boundary**: Port 8138 `-np 1`, `cache_prompt: False`, $\Delta \text{VRAM} \equiv 0.0\text{ MiB}$

## Operational Invariants

1. **Selective Uncertainty Gate $\Gamma(a_t)$**:
   - Verification gating must NEVER be evaluated blindly on every single step.
   - Read-only reconnaissance commands (`ast-grep outline`, `cat`, directory navigation) MUST short-circuit with `action_type="read_only"` (0 LLM inference calls).
   - Port 8138 logprob probes (`jev_decide`) are strictly triggered upon:
     a) Post-Strike-1 failure recovery ($S \ge 1$).
     b) High AST blast radius ($B(s) > 3$ callers).
     c) Explicit state mutation decisions (`action_type="mutate"`).

2. **KV Slot Cache Protection**:
   - Every auxiliary logprob probe dispatched to Port 8138 `/v1/completions` MUST pass `"cache_prompt": False`.
   - Modifying or invalidating the pinned session Longest Common Prefix (LCP) during auxiliary verification is strictly prohibited.

3. **Contractive Fixed-Point Attractor Invariant**:
   - All continuous vector deliberation updates must be contractive with Lipschitz constant $L < 1.0$, guaranteeing fixed-point convergence in $\le 6$ iterations.
