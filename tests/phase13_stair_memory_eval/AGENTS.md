# AGENTS.md — Phase 13 STAIR Structural ToC/AST & Memory Testbed Orientation

> **Project**: Hermes Agent OS — Phase 13 Evaluation Harness  
> **Literature**: IBM STAIR (arXiv:2609.03874), Anthropic 5-Layer Memory Hierarchy  
> **Target Scenario**: `scenario/polyglot_repo/` (Multi-tenant token claim validation across polyglot codebase)  
> **Verification Gate**: `pytest tests/phase13_stair_memory_eval/ -q && python3 -c "import json; d=json.load(open('tests/phase13_stair_memory_eval/metrics.json')); assert d['recall_at_1'] >= 0.826 and d['chunk_boundary_errors'] == 0 and d['phase13_certified'] is True"`

---

## 1. Goal Contract Standard

```text
/goal Refactor MultiTenantJwtAuthenticator.validate_claim_signature in scenario/polyglot_repo/auth_engine.py to support modern v2 token claims ('tenant_id' or 'tid' fallback) per specs/AUTH_SPEC.md, navigating via STAIR AST outline.

outcome:
  1. Inspect scenario/polyglot_repo/ using ast-grep outline.
  2. Locate validate_claim_signature within MultiTenantJwtAuthenticator.
  3. Apply a surgical patch supporting 'tenant_id' and 'tid' claim keys.
  4. All tests in scenario/polyglot_repo/test_polyglot_auth.py pass with exit code 0.

verify: pytest scenario/polyglot_repo/test_polyglot_auth.py -q
```
