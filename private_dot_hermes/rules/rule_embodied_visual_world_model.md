# rule_embodied_visual_world_model.md — Invariant Operating Rule for Embodied Visual World Models & Arc-AGUI Multimodal Desktop Parity

> **Target**: Hermes Agent OS & Arc-AGUI Multimodal Desktop Interaction Substrate  
> **Authority**: Phase 18 Architectural Standard (`Evolution.md` Section 3.7 & 4.1)  
> **Theoretical Grounding**: Google DeepMind / Harvard / Stanford (*Visual World Models for Action & Continual Learning*), Linux AT-SPI2 Accessibility Standards

---

## 1. Context & Architectural Mandate

In GUI desktop automation, stateless screenshot-to-coordinate clicking fails catastrophically whenever windows shift, layouts asynchronously reflow, or unpredicted modal dialogs appear. Hermes operates as an embodied visual world model combining structural OS accessibility trees with zero-CUDA-VRAM localized visual verification.

1. **Symbolic Widget Hierarchy (AT-SPI2)**:
   - Queries the Linux accessibility bus (`org.a11y.atspi`) via `at-spi2-core` in < 5ms entirely on CPU RAM.
   - Extracts complete widget hierarchies: `role`, `name`, `states`, `bounding_box`, and supported semantic actions (`click`, `activate`, `select`).
   - Window-Shift Invariant: Actions are targeted by semantic widget node identity rather than brittle absolute screen coordinates, ensuring 100% resilience to window relocation.

2. **Localized Dirty-Rectangle Inspection (Port 8139 CPU Vision Sidecar)**:
   - When visual state verification or OCR confirmation is required, Hermes crops only the active bounding rectangle ($\le 384 \times 384$ px) via standard Wayland / X11 tools (`grim` / `slurp`).
   - Dispatches cropped regions to `SmolVLM2-256M-Video-Instruct` on Port 8139 (`http://127.0.0.1:8139/v1/chat/completions`) configured with `CUDA_VISIBLE_DEVICES=""`, consuming **0 MiB CUDA VRAM**.

3. **Predictive Verification & Divergence Halting**:
   - Inside `<|channel>thought`, the planner explicitly predicts the expected post-action transition state $s_{t+1}^*$.
   - Following action dispatch, Hermes captures the actual post-action state $s_{t+1}$ and calculates structural divergence:
     $$D(s_{t+1}^*, s_{t+1}) = \text{Divergence}(s_{t+1}^*, s_{t+1})$$
   - If an unpredicted error modal, occlusion, confirmation dialog, or spinner stall is detected ($D > \tau$), Hermes halts immediately and invokes deliberative recovery rather than blindly continuing actions into an error state.
