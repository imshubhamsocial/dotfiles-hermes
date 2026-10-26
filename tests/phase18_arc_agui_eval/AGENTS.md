# AGENTS.md — Phase 18 Embodied Visual World Models & Zero-VRAM Arc-AGUI Multimodal Desktop Parity

> **Project**: Hermes Agent OS — Phase 18 Evaluation Harness  
> **Literature**: Google DeepMind / Harvard / Stanford (*Visual World Models for Action & Continual Learning*), Linux AT-SPI2 Accessibility Standards  
> **Target Scenario**: `scenario/` (Symbolic AT-SPI2 widget hierarchy, zero-CUDA localized dirty-crop inspection, predictive divergence & anomalous modal halt)  
> **Verification Gate**: `pytest tests/phase18_arc_agui_eval/ -q && python3 -c "import json; v=json.load(open('tests/phase18_arc_agui_eval/world_model_metrics.json')); assert v['port_8139_cuda_vram_mib'] == 0 and v['predictive_gui_verification_accuracy'] >= 0.95 and v['anomalous_modal_halt_triggered'] is True"`

---

## 1. Goal Contract Standard

```text
/goal Refactor GuiWorldModel in tests/phase18_arc_agui_eval/scenario/gui_world_model.py to enforce predictive divergence halting upon anomalous modal detection.

outcome:
  1. Inspect tests/phase18_arc_agui_eval/scenario/gui_world_model.py.
  2. Implement anomalous modal detection and predictive divergence calculation in step_and_verify.
  3. Ensure that when an unexpected modal dialog or divergence exceeds threshold tau, halt_triggered is set to True.
  4. All tests in tests/phase18_arc_agui_eval/scenario/test_gui_world_model.py pass with exit code 0.

verify: pytest tests/phase18_arc_agui_eval/scenario/test_gui_world_model.py -q
```
