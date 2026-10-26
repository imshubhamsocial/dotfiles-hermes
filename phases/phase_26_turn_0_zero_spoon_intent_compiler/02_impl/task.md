# Phase 26: Turn-0 Zero-Spoon Intent Compiler — Implementation Checklist

> **Phase Directory**: `phase_26_turn_0_zero_spoon_intent_compiler`  
> **Status**: Ready for Stage `02_impl` execution  

---

## 1. Targeted Symbols & Code Modules
- Target File(s): `tests/phase26_zero_spoon_eval/scenario/data_pipeline.py`
- Targeted Symbol(s): `DataPipeline.process_record`
- Causal Hypothesis: In `DataPipeline.process_record`, telemetry events are accessed via direct dictionary subscription `event_id = record["event_id"]`. When processing legacy telemetry payloads that omit the `event_id` field, an unhandled `KeyError` is raised. Replacing direct indexing with safe access `event_id = record.get("event_id", "UNKNOWN")` ensures legacy compatibility without compromising modern event handling, passing both unit tests and sealing the cryptographic verification receipt.

---

## 2. Surgical Implementation Plan
- [x] Step 1: Formulate single-cause causal hypothesis.
- [ ] Step 2: Ensure non-git backup exists (`<target>.hermes.bak`) if mutating Domain B files.
- [ ] Step 3: Apply mutation via `jev_mutate_module` adhering to Karpathy U12 15-line diff limit.
- [ ] Step 4: Verify pre-commit `ast.parse` and post-write `ruff check` pass with code 0.
- [ ] Step 5: Advance stage to `03_verify` in `03_verify/status.json`.
