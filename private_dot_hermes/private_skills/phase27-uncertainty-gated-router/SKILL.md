---
name: phase27-uncertainty-gated-router
description: Selective entropy and blast-radius gate
---

# Selective Uncertainty-Gated Decision Router (Phase 27)

## Overview
Phase 27 operationalizes the Princeton *Inference Scaling fLaws* (arXiv:2411.17501) and Apple *LoopCD* (arXiv:2610.02185) selective gating protocol. Rather than incurring negative returns through perpetual step-by-step verification, Hermes deploys an **Uncertainty Gate $\Gamma(a_t)$**.

## Gating Policy
1. **Read-Only Reconnaissance Bypass**:
   When `action_type == "read_only"`, short-circuit with 0 LLM calls (`gate_bypassed: True`, latency < 0.1 ms).
2. **Selective Probe Triggers**:
   A Port 8138 logprob probe is dispatched if and only if:
   - Strike Count $S \ge 1$ (post-failure recovery).
   - AST Blast Radius $B(s) > 3$ callers.
   - Action Mutates Core State (`action_type == "mutate"`).
3. **KV Cache Preservation**:
   All `/v1/completions` probes strictly pass `"cache_prompt": False`, preserving the pinned session KV cache on single-slot `-np 1`.
4. **Contractive Latent Deliberation**:
   When continuous vector guidance is needed, invoke `mcp_openjev(jev_latent_deliberate, vector=...)` for monotonic fixed-point attractor convergence ($\Delta^{(k)} < 0.01$).
