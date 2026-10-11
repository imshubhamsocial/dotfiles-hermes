# Rule: Native RSI Distillation Protocol

This rule governs the continuous closed-loop distillation of architectural and operational invariants, ensuring that learning patterns are permanently captured and integrated into the system's core knowledge base.

## Protocol Overview

The Native RSI (Runtime State Invariant) protocol mandates a dual-stream approach to knowledge persistence:

1. **Explicit Rule Authoring (The Loop):**
   - **Mechanism:** New, high-fidelity architectural invariants and derived principles must be explicitly authored by a designated expert or via a controlled workflow (e.g., using a dedicated `/loop learn` command or `write_file` followed by a dedicated processing step).
   - **Target:** Rules are initially authored as Markdown files within the canonical directory: `/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes/.hermes/rules/`.
   - **Goal:** To create durable, verifiable, and reviewable documentation of non-obvious, complex system behavior.

2. **Automatic Session Memory Consolidation (The Observer):**
   - **Mechanism:** The system incorporates an `on_session_end` observer hook. This hook automatically monitors and consolidates transient session data (e.g., debugging outputs, successful task completions, high-signal discussions) that meet established complexity thresholds.
   - **Target:** These consolidated memories are indexed into the OpenViking knowledge base (OpenViking) using `viking_remember` or similar indexing mechanisms.
   - **Goal:** To ensure that the practical experience of development and debugging contributes to the long-term, retrievable institutional knowledge base, minimizing knowledge loss between sessions.

## Implementation Flow

| Step | Action | Tool/Method | Output | Verification |
| :--- | :--- | :--- | :--- | :--- |
| **A. Authoring** | Write the rule definition. | `write_file` (or `/loop learn`) | `rule_native_rsi_distillation.md` | Existence check. |
| **B. Learning** | Ingest the rule into the system knowledge graph. | `/loop learn` | Rule incorporated into system prompts and internal knowledge structure. | System prompt inspection or dedicated validation command. |
| **C. Observation**| Allow the system to complete work. | `on_session_end` hook | Automated writes to OpenViking. | OpenViking API call/verification. |

## Constraints & Boundaries
* **Boundary 1:** All explicit rules must reside in `.../.hermes/rules/`.
* **Boundary 2:** The automatic consolidation must *never* capture low-signal or redundant conversational chaff; only verifiable, complex patterns qualify.
* **Constraint:** All mechanisms must use native upstream tools (e.g., built-in hooks, standard CLI features) and avoid bespoke Python files or custom daemons for core functionality.