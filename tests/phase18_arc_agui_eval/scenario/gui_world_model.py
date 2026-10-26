"""Embodied Visual World Model and Arc-AGUI Interaction Substrate (Phase 18).

Combines Linux AT-SPI2 symbolic accessibility trees with zero-CUDA-VRAM localized
bounding crops on Port 8139, implementing predictive state transition verification
and divergence halting upon anomalous modal detection.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class WidgetNode:
    """Represents a symbolic accessibility node in the AT-SPI2 tree."""
    id: str
    role: str
    name: str
    bbox: tuple[int, int, int, int]  # (x, y, width, height)
    is_modal: bool = False
    states: list[str] = field(default_factory=list)
    children: list[WidgetNode] = field(default_factory=list)

    def find_by_name(self, target_name: str) -> WidgetNode | None:
        """Recursively resolves a widget by semantic name."""
        if self.name == target_name:
            return self
        for child in self.children:
            res = child.find_by_name(target_name)
            if res is not None:
                return res
        return None

    def find_anomalous_modal(self) -> WidgetNode | None:
        """Recursively checks for error dialogs, alert modals, or blockers."""
        if self.is_modal or self.role in ("alert", "error_dialog", "modal_dialog"):
            return self
        for child in self.children:
            res = child.find_anomalous_modal()
            if res is not None:
                return res
        return None


@dataclass
class GuiState:
    """Represents full symbolic-visual desktop state."""
    window_offset: tuple[int, int] = (0, 0)
    root_widgets: list[WidgetNode] = field(default_factory=list)

    def find_widget(self, name: str) -> WidgetNode | None:
        """Resolves widget by name across all root hierarchy trees."""
        for root in self.root_widgets:
            found = root.find_by_name(name)
            if found is not None:
                return found
        return None

    def has_anomalous_modal(self) -> bool:
        """Returns True if any unpredicted modal or error alert exists."""
        for root in self.root_widgets:
            if root.find_anomalous_modal() is not None:
                return True
        return False


@dataclass
class GuiAction:
    """Represents a semantic GUI action dispatch."""
    action_type: str  # click, type, activate
    target_name: str
    payload: str | None = None


@dataclass
class StepResult:
    """Result of predictive step execution and verification."""
    success: bool
    divergence: float
    halt_triggered: bool
    post_state: GuiState
    message: str


class GuiWorldModel:
    """Embodied Visual World Model with predictive transition verification."""

    def __init__(self, threshold: float = 0.25):
        self.threshold = threshold
        self.port_8139_cuda_vram_mib: int = 0

    def query_vision_sidecar_cpu(self, crop_bbox: tuple[int, int, int, int]) -> dict[str, Any]:
        """Simulates CPU-bound SmolVLM2 query on Port 8139 (0 MiB CUDA VRAM)."""
        _x, _y, w, h = crop_bbox
        assert w <= 384 and h <= 384, f"Dirty-rectangle exceeds 384x384 ceiling: {w}x{h}"
        return {
            "endpoint": "http://127.0.0.1:8139/v1/chat/completions",
            "cuda_vram_mib": self.port_8139_cuda_vram_mib,
            "status": "ok",
            "text_ocr": "Confirmed",
        }

    def crop_dirty_rectangle(self, bbox: tuple[int, int, int, int], max_dim: int = 384) -> tuple[int, int, int, int]:
        """Calculates localized inspection crop bounded to max_dim x max_dim."""
        x, y, w, h = bbox
        crop_w = min(w, max_dim)
        crop_h = min(h, max_dim)
        return (x, y, crop_w, crop_h)

    def apply_window_shift(self, state: GuiState, dx: int, dy: int) -> GuiState:
        """Shifts all window coordinates, demonstrating AT-SPI2 symbolic resilience."""
        new_roots = []
        for root in state.root_widgets:
            rx, ry, rw, rh = root.bbox
            shifted_root = WidgetNode(
                id=root.id,
                role=root.role,
                name=root.name,
                bbox=(rx + dx, ry + dy, rw, rh),
                is_modal=root.is_modal,
                states=list(root.states),
                children=[],
            )
            for child in root.children:
                cx, cy, cw, ch = child.bbox
                shifted_root.children.append(
                    WidgetNode(
                        id=child.id,
                        role=child.role,
                        name=child.name,
                        bbox=(cx + dx, cy + dy, cw, ch),
                        is_modal=child.is_modal,
                        states=list(child.states),
                    )
                )
            new_roots.append(shifted_root)
        return GuiState(
            window_offset=(state.window_offset[0] + dx, state.window_offset[1] + dy),
            root_widgets=new_roots,
        )

    def predict_transition(self, current_state: GuiState, action: GuiAction) -> GuiState:
        """System-2 planner prediction of expected post-action state s_{t+1}^*."""
        predicted_roots = []
        for root in current_state.root_widgets:
            p_children = []
            for child in root.children:
                p_child = WidgetNode(
                    id=child.id,
                    role=child.role,
                    name=child.name,
                    bbox=child.bbox,
                    is_modal=child.is_modal,
                    states=list(child.states),
                )
                if child.name == action.target_name and action.action_type == "click":
                    p_child.states.append("activated")
                p_children.append(p_child)
            predicted_roots.append(
                WidgetNode(
                    id=root.id,
                    role=root.role,
                    name=root.name,
                    bbox=root.bbox,
                    is_modal=root.is_modal,
                    states=list(root.states),
                    children=p_children,
                )
            )
        return GuiState(window_offset=current_state.window_offset, root_widgets=predicted_roots)

    def compute_divergence(self, predicted: GuiState, actual: GuiState) -> float:
        """Computes structural divergence D(s*, s).

        Returns value in [0.0, 1.0]. Divergence spikes when unpredicted modals
        appear or expected widget states fail to materialize.
        """
        divergence = 0.0

        # Modal anomaly penalty: Unpredicted modal induces heavy divergence spike
        if actual.has_anomalous_modal() and not predicted.has_anomalous_modal():
            divergence += 0.85

        # Check target widget state mismatch
        for p_root in predicted.root_widgets:
            for p_child in p_root.children:
                a_child = actual.find_widget(p_child.name)
                if a_child is None:
                    divergence += 0.30
                else:
                    if set(p_child.states) != set(a_child.states):
                        divergence += 0.15

        return min(divergence, 1.0)

    def step_and_verify(
        self,
        current_state: GuiState,
        action: GuiAction,
        actual_post_state: GuiState,
    ) -> StepResult:
        """Executes action, computes divergence against prediction, and enforces halt."""
        predicted_state = self.predict_transition(current_state, action)
        divergence = self.compute_divergence(predicted_state, actual_post_state)

        # Enforce predictive divergence and anomalous modal halting
        halt_triggered = bool(
            (divergence > self.threshold) or actual_post_state.has_anomalous_modal()
        )

        success = not halt_triggered
        msg = "Step verified cleanly" if success else "Halted: Divergence or anomalous modal detected"
        return StepResult(
            success=success,
            divergence=divergence,
            halt_triggered=halt_triggered,
            post_state=actual_post_state,
            message=msg,
        )
