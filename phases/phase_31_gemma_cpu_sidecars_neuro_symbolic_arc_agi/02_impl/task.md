# Phase 31: Gemma CPU Sidecars & Neuro-Symbolic ARC-AGI — Implementation Checklist

> **Phase Directory**: `phase_31_gemma_cpu_sidecars_neuro_symbolic_arc_agi`  
> **Status**: Completed Stage `02_impl` execution  

---

## 1. Targeted Symbols & Code Modules
- Target File(s): `.hermes/mcp_openjev.py`
- Target Symbol: `jev_gemma_sidecar_embed_and_refine`, `jev_arc_agi_neurosymbolic_solve`
- Module Stems: `mcp_openjev`
- Required Skills: `karpathy-surgical-diff`, `viking-retrieval`

---

## 2. Surgical Implementation Plan
- [x] Step 1: Formulate single-cause causal hypothesis:
  - **Hypothesis**: In `_GemmaCPUSidecarPool`, in-process EmbeddingGemma 2 (256d MRL) and T5Gemma 2 perform fast CPU RAM ranking and program synthesis. Verifying L2-normalization, latency < 25 ms, and RHAE score = 1.0 guarantees zero-GPU-overhead neuro-symbolic inference.
- [x] Step 2: Ensure non-git backup exists (`<target>.hermes.bak`) if mutating Domain B files.
- [x] Step 3: Apply mutation via `jev_mutate_module` adhering to Karpathy U12 15-line diff limit.
- [x] Step 4: Verify pre-commit `ast.parse` and post-write `ruff check` pass with code 0.
- [x] Step 5: Advance stage to `03_verify` in `03_verify/status.json`.
