---
name: sympy-spec-regenerator
description: "SymPy VRAM proof & spec codegen"
---

# SymPy VRAM Proof & Spec-Driven Regeneration

## Overview
This skill governs algebraic verification and spec-driven code synthesis using symbolic cost bounds. Prior to regenerating any core module or mounting external MCP tools, Hermes verifies that the hardware VRAM boundary ($\le 4,812\text{ MiB}$) is algebraically respected on CPU RAM.

## Symbolic VRAM Cost Model
The analytical memory equation for local inference under speculative decoding is:

$$\text{VRAM}_{\text{total}} = \text{VRAM}_{\text{weights}} + \text{VRAM}_{\text{MTP}} + 2 \cdot n_{\text{layers}} \cdot n_{\text{kv\_heads}} \cdot d_{\text{head}} \cdot c_{\text{ctx}} \cdot b_{\text{quant}} + \Delta_{\text{tool}} \le 4,812\text{ MiB}$$

### Key Parameters (Gemma-4-E4B-it-Heretic):
- $\text{VRAM}_{\text{weights}}$: $2,850\text{ MiB}$ (Q4_K_M model weights)
- $\text{VRAM}_{\text{MTP}}$: $420\text{ MiB}$ (Bartowski MTP draft weights)
- $n_{\text{layers}}$: $28$ layers
- $n_{\text{kv\_heads}}$: $4$ heads (Grouped-Query Attention)
- $d_{\text{head}}$: $256$ dimensions
- $b_{\text{quant}}$: $0.5625\text{ bytes}$ ($4.5\text{-bit}$ Q4_0 KV cache)
- $c_{\text{ctx}}$: $131,072\text{ tokens}$ ($128\text{K}$ context window)
- $\Delta_{\text{tool}}$: $0\text{ MiB}$ (all AST, vector embeddings, and MCP run on CPU)

## Procedure
1. **Load Design Spec**: Read symbolic constraints from `specs/<subsystem>.md`.
2. **Algebraic Proof**: Run SymPy on CPU to verify that total memory does not breach $4,812\text{ MiB}$.
3. **Regenerative Synthesis**: Generate code satisfying input/output contract assertions with zero floating-point roundoff error ($< 10^{-6}$).
4. **Epistemic Closure**: Execute pytest to confirm deterministic pass before committing.
