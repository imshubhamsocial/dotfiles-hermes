# Process Knowledge Base & Failure Mode Taxonomy
## Distilled Learnings from Multi-Bot Benchmark Runs, Hardware Envelopes & Antigravity Metacognitive Logs

> **Document ID**: `docs/PROCESS_KNOWLEDGE_BASE.md`  
> **Source Corpus**: `docs/ANTIGRAVITY_ORCHESTRATOR_LEDGER.md` & `docs/HERMES_HARNESS_JOURNEY_AND_LEARNINGS.md`  
> **Classification**: Master Process Knowledge Base (Phase 1 Deliverable)

---

## 1. Process Learning Registry

```yaml
- id: PL-001
  category: "context_management"
  failure_mode: "Context Compaction Freeze at 130+ messages"
  root_cause: "Unbounded session length without 3-turn reset"
  process_rule: "ALWAYS reset session after 3 turns. Fresh context reads disk as ground truth in ~1500 tokens."
  source: "Journey §4.1, Ledger §4"
  applicable_to: ["any_agent", "any_project"]
  priority: "P0"

- id: PL-002
  category: "plan_decomposition"
  failure_mode: "Single-turn monolithic hallucination and syntax degradation"
  root_cause: "Asking 4B SLMs to synthesize multiple complex subsystems in one turn"
  process_rule: "ALWAYS decompose tasks into single-responsibility modular turns (1 subsystem per turn)."
  source: "Journey §4.2, Ledger §5"
  applicable_to: ["slm_coder", "architect"]
  priority: "P0"

- id: PL-003
  category: "plan_decomposition"
  failure_mode: "Hallucinated physical constants and floating-point drift"
  root_cause: "Passing natural language prose descriptions instead of explicit mathematical formulas"
  process_rule: "ALWAYS supply architectural blueprints with explicit numerical constants and PDE boundary equations."
  source: "Journey §4.3, Ledger §3"
  applicable_to: ["architect", "coder"]
  priority: "P0"

- id: PL-004
  category: "verification"
  failure_mode: "False-positive test passes on non-functioning scenes"
  root_cause: "Brittle DOM / existence checks that do not test runtime dynamics"
  process_rule: "ALWAYS verify dynamic physical invariants (velocities, spatial bounds, memory arrays) via headless WebGL/Playwright."
  source: "Journey §3.B, Ledger §7"
  applicable_to: ["tester"]
  priority: "P0"

- id: PL-005
  category: "context_management"
  failure_mode: "Patch precision and attention decay after extended turns"
  root_cause: "Accumulation of historical conversational noise"
  process_rule: "Prune historical turns using DifferentialStateCompactor to maintain context < 400 tokens."
  source: "Journey §3.A, Ledger §25"
  applicable_to: ["orchestrator", "token_engine"]
  priority: "P1"

- id: PL-006
  category: "scope_management"
  failure_mode: "Duplicate variable declaration patch trap ('Identifier X has already been declared')"
  root_cause: "Unstructured search-and-replace in global JavaScript/TypeScript scope"
  process_rule: "NEVER declare variables in global scope; encapsulate all scene variables in single-namespace state objects."
  source: "Ledger §4, §7"
  applicable_to: ["coder"]
  priority: "P0"

- id: PL-007
  category: "compute_optimization"
  failure_mode: "Context saturation from redundant tool schemas"
  root_cause: "Loading all 20+ tool definitions into every bot regardless of role"
  process_rule: "Prune tool schemas strictly per role (architect=read/web, coder=file/terminal, tester=terminal)."
  source: "Ledger §25, §26"
  applicable_to: ["runner", "capability_masks"]
  priority: "P0"

- id: PL-008
  category: "spatial_integration"
  failure_mode: "Disjoint floating components and clipped visual meshes"
  root_cause: "Failing to define a Universal Spatial Coordinate Contract (USCC) before rendering"
  process_rule: "Declare explicit bounding volumes (Tank={w:36, h:22, d:24}, WaterY=6) in Step 1 before placing meshes."
  source: "Ledger §32"
  applicable_to: ["architect", "coder"]
  priority: "P0"

- id: PL-009
  category: "verification"
  failure_mode: "Premature rollbacks on progressive multi-step builds"
  root_cause: "All-or-nothing test assertions evaluating future-stage components"
  process_rule: "Use progressive milestone assertion gates tailored to the current build step."
  source: "Ledger §27"
  applicable_to: ["tester", "grader"]
  priority: "P1"

- id: PL-010
  category: "scope_management"
  failure_mode: "Runtime null-reference on Three.js mesh positioning"
  root_cause: "Instantiating or setting position before mesh geometry/material construction"
  process_rule: "ALWAYS follow strict lifecycle order: Geometry -> Material -> Mesh -> Position -> Scene.add."
  source: "Ledger §29"
  applicable_to: ["coder"]
  priority: "P0"

- id: PL-011
  category: "verification"
  failure_mode: "Silent syntax errors committed to filesystem"
  root_cause: "Bypassing pre-commit AST and brace balance validation"
  process_rule: "ALL generated code artifacts must pass through ObserverGate and LiveLSP before disk commit."
  source: "Ledger §23, §74"
  applicable_to: ["observer_gate", "lsp_bridge"]
  priority: "P0"

- id: PL-012
  category: "compute_optimization"
  failure_mode: "GPU VRAM out-of-memory contention with local SLMs"
  root_cause: "Running dense neural embedding models on the same GPU as the LLM"
  process_rule: "Run neural embeddings (BGE-Small ONNX) strictly on CPU with 0 MB GPU VRAM consumption."
  source: "Ledger §70"
  applicable_to: ["embeddings", "agent_os"]
  priority: "P0"
```
