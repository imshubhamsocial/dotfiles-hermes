"""Benchmark and Verification Script for Phase 18 Arc-AGUI Embodied Visual World Model."""

import json
import os
import pathlib
import sys

testbed_root = pathlib.Path(__file__).resolve().parent
scenario_dir = testbed_root / "scenario"
sys.path.insert(0, str(testbed_root))
sys.path.insert(0, str(scenario_dir))

from gui_world_model import (
    GuiAction,
    GuiState,
    GuiWorldModel,
    WidgetNode,
)


def run_benchmark():
    model = GuiWorldModel(threshold=0.25)

    # 1. Test Window Shift Resilience across 50 simulated window positions
    shift_success = 0
    total_shifts = 50
    base_btn = WidgetNode(id="b1", role="push_button", name="Save", bbox=(10, 20, 60, 25))
    base_win = WidgetNode(id="w1", role="window", name="App", bbox=(0, 0, 300, 200), children=[base_btn])
    state = GuiState(root_widgets=[base_win])

    for i in range(total_shifts):
        dx = (i * 13) % 200
        dy = (i * 17) % 150
        shifted = model.apply_window_shift(state, dx, dy)
        found = shifted.find_widget("Save")
        if found is not None and found.bbox == (10 + dx, 20 + dy, 60, 25):
            shift_success += 1

    window_shift_pass = (shift_success == total_shifts)

    # 2. Test Localized Dirty-Rectangle and Zero-CUDA VRAM
    crop = model.crop_dirty_rectangle((10, 20, 500, 500), max_dim=384)
    sidecar_resp = model.query_vision_sidecar_cpu(crop)
    port_8139_vram = sidecar_resp.get("cuda_vram_mib", 0)

    # 3. Test Predictive GUI Verification Accuracy
    correct_predictions = 0
    total_predictions = 40
    for i in range(total_predictions):
        action = GuiAction(action_type="click", target_name="Save")
        pred = model.predict_transition(state, action)
        w = pred.find_widget("Save")
        if w is not None and "activated" in w.states:
            correct_predictions += 1
    accuracy = correct_predictions / total_predictions

    # 4. Test Anomalous Modal Halting
    alert_node = WidgetNode(id="a1", role="alert", name="Error", bbox=(50, 50, 100, 80), is_modal=True)
    state_err = GuiState(root_widgets=[base_win, alert_node])
    res_err = model.step_and_verify(state, GuiAction("click", "Save"), state_err)
    halt_triggered = res_err.halt_triggered

    metrics = {
        "port_8139_cuda_vram_mib": port_8139_vram,
        "predictive_gui_verification_accuracy": accuracy,
        "anomalous_modal_halt_triggered": halt_triggered,
        "anomaly_modal_halted": halt_triggered,
        "window_shift_resilience_pass": window_shift_pass,
    }

    # Write metrics to both world_model_metrics.json and agui_world_metrics.json
    (testbed_root / "world_model_metrics.json").write_text(json.dumps(metrics, indent=2))
    (testbed_root / "agui_world_metrics.json").write_text(json.dumps(metrics, indent=2))

    print(f"Phase 18 benchmark metrics generated: {metrics}")
    return metrics


if __name__ == "__main__":
    run_benchmark()
