# Phase 18: Embodied Visual World Model (SmolVLM2 \+ AT-SPI2) — Implementation Checklist

> **Phase Directory**: `phase_18_embodied_visual_world_model_smolvlm2_at_spi2`  
> **Status**: Completed Stage `02_impl`, ready for Stage `03_verify`  

---

## 1. Targeted Symbols & Code Modules
- Target File(s): `tests/phase18_arc_agui_eval/scenario/gui_world_model.py`
- Target Symbol: `GuiWorldModel.step_and_verify`
- Module Stems: `gui_world_model`
- Required Skills: `karpathy-surgical-diff`

---

## 2. Surgical Implementation Plan
- [x] Step 1: Formulate single-cause causal hypothesis:
  - Causal hypothesis: `GuiWorldModel.step_and_verify` hardcodes `halt_triggered = False`, preventing the world model from halting when anomalous modal dialogs appear or when divergence exceeds `self.threshold`. Updating `halt_triggered = bool((divergence > self.threshold) or actual_post_state.has_anomalous_modal())` properly triggers halts and ensures `success = not halt_triggered`, resolving test failures in `test_gui_world_model.py` and `test_verify.py`.
- [x] Step 2: Ensure non-git backup exists (`<target>.hermes.bak`) if mutating Domain B files (Domain C repo: shadow backup created at `tests/phase18_arc_agui_eval/scenario/gui_world_model.py.hermes.bak`).
- [x] Step 3: Apply mutation via `jev_mutate_module` adhering to Karpathy U12 15-line diff limit.
- [x] Step 4: Verify pre-commit `ast.parse` and post-write `ruff check` pass with code 0.
- [x] Step 5: Advance stage to `03_verify` in `03_verify/status.json`.
