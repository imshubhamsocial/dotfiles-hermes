---
name: antigravity-artifacts
description: Produce Google DeepMind Antigravity 2.0 (AGY) compliant deliverables with GitHub alerts, Mermaid flowcharts, carousels, and standalone Generative UI HTML auxiliary apps.
tags: [antigravity, agy, artifacts, mermaid, generative-ui, html]
---

# Antigravity 2.0 Artifacts Engine

Use this skill when generating deliverables, architectural reports, telemetry dashboards, or visual summaries for Google Antigravity 2.0.

## Output Formatting Standards

1. **Artifact Location**:
   - Save persistent artifacts into `<appDataDir>/brain/<conversation-id>/`
   - Store temporary datasets or scratch scripts into `scratch/`

2. **GitHub-Style Alerts**:
   - `> [!NOTE]` — Background context or implementation details.
   - `> [!TIP]` — Efficiency and optimization tips.
   - `> [!IMPORTANT]` — Essential non-negotiable requirements and constraints.
   - `> [!WARNING]` — Breaking changes or operational hazards.
   - `> [!CAUTION]` — Critical risks (data loss, VRAM overflow).

3. **Mermaid Diagrams**:
   - Supported: `flowchart TD/LR`, `sequenceDiagram`, `stateDiagram-v2`, `classDiagram`, `erDiagram`, `xychart-beta`.
   - Always quote node labels with parentheses: `id["Step (Verifying)"]`.

4. **Carousels**:
   - Enclose with four backticks: ````carousel ... <!-- slide --> ... ````

5. **HTML Auxiliary Apps**:
   - Standalone single-file HTML/JS/CSS bundles equipped with KaTeX, Chart.js, and Canvas for DOM-isolated live preview in the auxiliary pane.
