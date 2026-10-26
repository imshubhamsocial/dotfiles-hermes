# Phase 13: STAIR Structural AST & 5-Layer Memory — Implementation Checklist

> **Phase Directory**: `phase_13_stair_structural_ast_5_layer_memory`  
> **Status**: Stage `02_impl` execution  

---

## 1. Targeted Symbols & Code Modules
- **Target File**: `tests/phase13_stair_memory_eval/scenario/polyglot_repo/auth_engine.py`
- **Target Symbol**: `MultiTenantJwtAuthenticator.validate_claim_signature`
- **Causal Hypothesis**: `MultiTenantJwtAuthenticator.validate_claim_signature` retrieves `token_payload.get("tenant")`. On modern v2 tokens, the tenant identifier is keyed under `"tenant_id"` or `"tid"`. Changing the extraction to `token_payload.get("tenant") or token_payload.get("tenant_id") or token_payload.get("tid")` enables successful validation across legacy, modern v2, and compact token schemas.
- **Karpathy U12 Limit**: Single causal mutation <= 15 lines diff.

---

## 2. Surgical Implementation Plan
- [x] Step 1: Formulate single-cause causal hypothesis for `MultiTenantJwtAuthenticator.validate_claim_signature`.
- [ ] Step 2: Ensure shadow backup (`<target>.hermes.bak`) exists.
- [ ] Step 3: Apply mutation via `jev_mutate_module` adhering to Karpathy U12 diff limit (<= 15 lines).
- [ ] Step 4: Verify pre-commit `ast.parse` and post-write `ruff check` pass with code 0.
- [ ] Step 5: Advance stage to `03_verify` in `03_verify/status.json`.
