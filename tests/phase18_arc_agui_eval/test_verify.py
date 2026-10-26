"""Verification test suite for Phase 18 metrics and gate criteria."""

import json
import pathlib
import sys

import pytest

testbed_root = pathlib.Path(__file__).resolve().parent
scenario_dir = testbed_root / "scenario"
sys.path.insert(0, str(scenario_dir))

from gui_world_model import (
    GuiAction,
    GuiState,
    GuiWorldModel,
    WidgetNode,
)


def test_world_model_metrics_verification():
    """Asserts that benchmark metrics meet all Phase 18 criteria."""
    report_file = testbed_root / "world_model_metrics.json"
    assert report_file.exists(), "world_model_metrics.json must be generated prior to verification"
    report = json.loads(report_file.read_text(encoding="utf-8"))

    assert report.get("port_8139_cuda_vram_mib") == 0
    assert report.get("predictive_gui_verification_accuracy", 0.0) >= 0.95
    assert report.get("anomalous_modal_halt_triggered") is True
    assert report.get("window_shift_resilience_pass") is True


def test_live_world_model_halt_enforcement():
    """Directly verifies that GuiWorldModel enforces halt when modal occurs."""
    model = GuiWorldModel(threshold=0.25)
    btn = WidgetNode(id="b1", role="push_button", name="OK", bbox=(10, 10, 50, 30))
    state = GuiState(root_widgets=[btn])

    err = WidgetNode(id="err", role="alert", name="Crash", bbox=(0, 0, 100, 100), is_modal=True)
    post_err = GuiState(root_widgets=[btn, err])

    res = model.step_and_verify(state, GuiAction("click", "OK"), post_err)
    assert res.halt_triggered is True
    assert res.divergence > 0.25
