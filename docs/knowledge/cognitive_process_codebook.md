# Cognitive Process Codebook
## Master Operational Rules for Autonomous SLM Multi-Agent Coordination

> **Document ID**: `docs/COGNITIVE_PROCESS_CODEBOOK.md`  
> **Status**: Active Reference (Phase 2 Deliverable)  
> **Target Models**: Gemma-4-E4B, Qwen-3.6-4B, OmniRouter, Antigravity Supervisor

---

## Rule 1: The 3-Turn Context Window Boundary
* Any agent context accumulating more than 3 turns MUST be pruned or reset.
* Read disk state directly using bounded AST outlines rather than relying on stale conversational memory.

## Rule 2: Single-Responsibility Modular Synthesis
* Never prompt an SLM to implement more than 1 subsystem per generation turn.
* Each generation turn must implement an in-degree 0 node from the SQLite Task DAG.

## Rule 3: Mathematical Contract Primacy
* Blueprints from `@architect` must declare explicit numerical constants, coordinate bounds, damping factors, and equation formulations.
* Prose explanations are secondary; deterministic numbers and formulas are mandatory.

## Rule 4: Single-Namespace State Containment
* Code generated in JavaScript/TypeScript/Python must contain variables within a single structured object (e.g., `const SIM = { ... }`).
* Global variable re-declarations are hard-blocked by pre-commit linters.

## Rule 5: Deterministic Zero-Sorry Invariant Testing
* Headless verification (Playwright, AST linter, Pytest) serves as infallible ground truth.
* No self-grading by language models; verify actual physical dynamics, bounding boxes, and velocity vectors.

## Rule 6: Pre-Commit Observer & LSP Gating
* Before writing to disk, code artifacts must pass AST syntax parsing, brace balancing, and type diagnostics.
* Invalid payloads are rejected instantly with line-level diagnostic feedback.

## Rule 7: Zero GPU VRAM Contention for Semantic Search
* All embedding models (`bge-small-en-v1.5` ONNX) execute exclusively on host CPU.
* Guaranteed 0 MB GPU VRAM overhead, preserving 100% of GPU compute for the 4B SLM inference engine.

## Rule 8: Asymmetric Cognitive Reasoning Allocation
* `@architect` runs with `reasoning_effort: high` for topological DAG planning.
* `@coder` and `@tester` run with `reasoning_effort: medium` for high-throughput deterministic execution.

## Rule 9: Btrfs NOCOW & RAMDisk Ephemeral Protection
* High-frequency logs, trajectory chains, and SQLite databases must use `chattr +C` (NOCOW).
* Ephemeral caches are stored in `/dev/shm` to protect NVMe endurance.

## Rule 10: Fast-Path Single-Query System Audits
* Always use unified sub-50ms helper scripts (`bin/audit_system_state.py`) instead of fragmented multi-command queries.

## Rule 11: Metacognitive Experience Mining & Negative Constraints
* Failures recorded in the `ExperienceStore` automatically generate negative constraints (`NEVER do X`) for subsequent prompts.
* Successes generate positive reusable playbooks (`ALWAYS do Y`).

## Rule 12: Programmatic RLM Kernel Dispatch
* Prefer batching multiple tool operations inside a persistent Python kernel session over sequential single-turn chat tool calling.
