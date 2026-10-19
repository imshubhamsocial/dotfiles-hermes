---
name: arc-agui-world-model
description: "Port 8139 SmolVLM2 + AT-SPI GUI model"
---

# Arc-AGUI Embodied Visual World Model Playbook (Phase 18)

When executing desktop GUI automation and visual verification under `<focus id="gui_world_model">`:

1. **Symbolic Accessibility Hierarchy Query (AT-SPI2)**:
   - Inspect the desktop accessibility tree via `org.a11y.atspi` on CPU RAM.
   - Resolve target widgets by semantic role and label rather than raw coordinates.
   - Guarantees complete resilience against window repositioning and desktop resolution shifts.

2. **Zero-CUDA-VRAM Localized Crop Inspection (Port 8139)**:
   - For visual state confirmation or OCR, isolate bounding box regions up to 384x384 px.
   - Query SmolVLM2 vision sidecar at loopback port 8139 with CPU execution.
   - Strictly enforces zero CUDA VRAM overhead, preserving GPU memory for core LLM inference.

3. **Predictive Transition & Divergence Halting**:
   - Model the expected transition state before dispatching any mouse or keyboard action.
   - Compare post-action observed hierarchy against predicted state.
   - If structural divergence exceeds threshold or an unpredicted modal appears, halt immediately.
