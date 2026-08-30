---
name: generative-ui-artifact
category: software-development
description: Generate zero-dependency, standalone interactive HTML/WebGL UI artifacts.
---

# Generative UI Artifacts Standard (Antigravity 2.0 Native Interface)

When the user asks to "visualize", "show me a dashboard of", "create an interactive simulation of", or invokes `/generative_ui`:

## Core Operational Invariants
1. **Zero-Dependency Portability**: Every artifact must be a single standalone `.html` file. CSS and JavaScript must be embedded inline or reference pre-cached libraries in `~/.hermes/assets/js/`.
2. **Local Render Target**: Write artifacts to `/dev/shm/hermes_artifacts/<session_id>_<name>.html` during active iterations, and persist to `~/.hermes/artifacts/<name>.html` upon completion.
3. **Interactive Capabilities**:
   - **Metrics & Dashboards**: Use Chart.js or pure SVG/Canvas with dark-mode responsive styling.
   - **3D Simulations**: Use Three.js r168 with WebGL requestAnimationFrame orbit loops and dynamic motion assertions ($\Delta\text{pos} > 0.001$).
   - **Data Explorers**: Use pure CSS Grid + vanilla JS searchable/sortable tables.
   - **Equations & Proofs**: Use KaTeX for mathematical formulas.
4. **Execution Protocol**:
   - Emit the complete HTML document.
   - Provide the exact local path and launch command: `xdg-open file:///dev/shm/hermes_artifacts/<name>.html`.
