---
name: phase16-experience-lesson-distiller
phase: "Phase 16"
authority: "DreamRSI Offline Replay & Lesson Distillation"
description: "DreamRSI trace lesson distiller"
---
# Experience Lesson Distiller Playbook (Phase 16)

When processing completed agent trajectories under `<focus id="experience_distillation">`:

1. **Replay Simulator Trace Ingestion (100% CPU)**:
   - Extract decision sequences from `telemetry/traces.jsonl`.
   - Map tool executions to replay nodes: `(state_hash, focus_regime, tool_name, diff_lines, attended_tokens, duration_ms, pytest_exit_code)`.
   - Store simulation world trees inside `.hermes/cache/dream_worlds/<task_hash>.json`.

2. **Counterfactual Dreaming & Branch Pruning**:
   - Trace dead-end tool actions that resulted in consecutive failures (Tabu triggers).
   - Simulate branch substitutions against cached disk trees to identify optimal tool sequencing.
   - Record simulated call reduction ratios in `EXPERIENCE.md`.

3. **Sequential MASS 3-Pass Validation**:
   - Pass A: Identify failure modes and unpruned context saturation.
   - Pass B: Formulate surgical skill and prompt mutations ($\le 40$-char frontmatter).
   - Pass C: Assert zero test-suite leakage (no evaluation repository directory references or mock assertions).

4. **RRSI Stability Gate**:
   - Confirm that $\mu(H') - s^* \ge 1.0 \cdot \sigma_0$.
   - Reject any mutation failing held-out test suites.
