---
name: phase26-zero-spoon-intent-compiler
description: "Zero-spoon-feeding intent AST compiler"
version: 1.0.0
phase: 26
tier: 4
---

# Phase 26: Zero-Spoon-Feeding Turn-1 Intent Compiler

## Overview
Grounded in Attention Physics (Gemma-4-E4B 128K context, SWA horizon 4,096 tokens) and Google Harness² 8-component decomposition (arXiv:2610.14224). Converts raw, un-spoon-fed natural language user prompts into internal execution contracts at Turn 1 via `mcp_openjev(jev_compile_intent)`.

## Turn-1 Dispatch Protocol
1. **Raw Natural Prompt Ingestion**:
   When receiving unstructured requests (e.g., *"Fix the KeyError in DataPipeline when processing legacy telemetry records"*), do NOT ask the human operator for `/goal` schemas, outcome strings, or negative constraints.
2. **Turn-1 Intent Compilation**:
   Under `<global>` declarative attention, invoke:
   ```json
   {
     "name": "jev_compile_intent",
     "arguments": {
       "raw_prompt": "<user_prompt>",
       "workspace_dir": "."
     }
   }
   ```
3. **Execution Manifest Ingestion**:
   `jev_compile_intent` returns in <35 ms on CPU RAM:
   - `security_passed`: Sanitization against command/prompt injections.
   - `shannon_entropy`: Input randomness measure ($H > 4.6$ threshold).
   - `attention_regime`: Automatic transition to `<focus id="<symbol>">`.
   - `ast_symbols`: Exact line-range outline (`L<start>-L<end>`).
   - `recommended_skills`: Top phase skills to hydrate via `skill_view`.
   - `inferred_verify_cmd`: Auto-detected verification target (`pytest -q`).
   - `negative_constraints`: Ambient enforcement of NC-001, NC-002, NC-003.
4. **Focused Execution & Closure**:
   Hydrate the recommended skill, apply the surgical diff ($\le 15$ lines), run `inferred_verify_cmd`, and verify `/tmp/hermes_verified_receipt.json` (exitstatus 0).
