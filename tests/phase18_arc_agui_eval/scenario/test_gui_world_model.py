"""Unit tests for GuiWorldModel (Phase 18)."""

import pytest
from gui_world_model import (
    GuiAction,
    GuiState,
    GuiWorldModel,
    WidgetNode,
)


def make_sample_desktop_state() -> GuiState:
    """Helper creating a sample desktop application state."""
    btn_submit = WidgetNode(
        id="btn_1",
        role="push_button",
        name="Submit",
        bbox=(100, 150, 80, 30),
        states=["enabled"],
    )
    btn_cancel = WidgetNode(
        id="btn_2",
        role="push_button",
        name="Cancel",
        bbox=(200, 150, 80, 30),
        states=["enabled"],
    )
    win_main = WidgetNode(
        id="win_main",
        role="window",
        name="MainForm",
        bbox=(50, 50, 400, 300),
        children=[btn_submit, btn_cancel],
    )
    return GuiState(window_offset=(50, 50), root_widgets=[win_main])


def test_window_shift_resilience():
    """Asserts that symbolic AT-SPI lookup resolves widgets across window relocation."""
    model = GuiWorldModel()
    state = make_sample_desktop_state()

    # Shift window by (120, 80) pixels
    shifted = model.apply_window_shift(state, dx=120, dy=80)

    # Symbolic lookup succeeds
    node = shifted.find_widget("Submit")
    assert node is not None
    assert node.bbox == (100 + 120, 150 + 80, 80, 30)

    # Brittle absolute coordinate check (100, 150) would hit empty background
    orig_x, orig_y = (100, 150)
    assert not (node.bbox[0] <= orig_x <= node.bbox[0] + node.bbox[2] and node.bbox[1] <= orig_y <= node.bbox[1] + node.bbox[3])


def test_localized_dirty_crop_and_zero_vram():
    """Asserts dirty-rectangle crop bounded to 384x384 and 0 MiB CUDA VRAM on Port 8139."""
    model = GuiWorldModel()
    crop = model.crop_dirty_rectangle((50, 50, 600, 400), max_dim=384)
    assert crop[2] <= 384 and crop[3] <= 384

    res = model.query_vision_sidecar_cpu(crop)
    assert res["cuda_vram_mib"] == 0
    assert res["status"] == "ok"


def test_normal_transition_verification():
    """Asserts clean transition without divergence or halts on expected action."""
    model = GuiWorldModel()
    state = make_sample_desktop_state()
    action = GuiAction(action_type="click", target_name="Submit")

    # Actual state matches expected post-action
    expected_actual = model.predict_transition(state, action)
    result = model.step_and_verify(state, action, expected_actual)

    assert result.success is True
    assert result.divergence == 0.0
    assert result.halt_triggered is False


def test_anomalous_modal_divergence_and_halt():
    """Asserts that unexpected error modal triggers divergence spike and immediate halt."""
    model = GuiWorldModel(threshold=0.25)
    state = make_sample_desktop_state()
    action = GuiAction(action_type="click", target_name="Submit")

    # Simulate anomalous error dialog appearing unexpectedly
    error_modal = WidgetNode(
        id="modal_err",
        role="alert",
        name="Database Connection Error",
        bbox=(120, 100, 250, 120),
        is_modal=True,
    )
    actual_state_with_error = GuiState(
        window_offset=(50, 50),
        root_widgets=list(state.root_widgets) + [error_modal],
    )

    result = model.step_and_verify(state, action, actual_state_with_error)

    assert result.divergence > 0.25
    assert result.halt_triggered is True, "Anomalous modal MUST trigger halt_triggered = True!"
    assert result.success is False
