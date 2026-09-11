---
name: agent-os-architecture
description: Architecture patterns and cognitive subsystems of Hermes OS.
version: 1.0.0
author: Hermes
platforms: [linux]
metadata:
  hermes:
    tags: [Architecture, Concepts, SecondBrain, Invariants]
    category: software-development
---

# Hermes Agent OS Architecture

Autonomous cognitive architecture patterns and invariant specifications for Hermes Agent OS. Documents System-2 deliberation loops, low-rank adaptation, Shannon entropy clarification gates, AST structural linting, and knowledge topology.

## When to Use

- Inspecting system invariants, hardware bounds, and memory hierarchies.
- Reviewing subsystem designs: ADK orchestrator, NeMo guardrails, Cactus uncertainty, or NoRA adaptation.
- Designing new plugins or lifecycle hooks conforming to native Hermes standards.

## Prerequisites

- Local inference server active at `http://127.0.0.1:8138/v1`.
- FastEmbed BGE CPU ONNX runtime for zero-VRAM semantic retrieval.
- Tree-sitter / ast-grep-py and Biome installed for structural validation.

## How to Run

Load any architectural subsystem reference on demand with the `skill_view` or `read_file` tool:

```bash
# Example: inspect Cactus Shannon entropy gate
skill_view(file_path="references/cactus-uncertainty.md")
```

## Quick Reference: Architecture Vault Index

| Concept / Reference | Subsystem Focus | Description |
|:---|:---|:---|
| `references/adk-orchestrator.md` | Multi-Agent Orchestration | Google ADK 2.8.0 topological DAG orchestration and runner execution. |
| `references/cactus-uncertainty.md` | Safety & Clarification Gate | Live Shannon entropy ($H = -\sum p\ln p$) gating high-uncertainty tool mutations. |
| `references/embedding-gemma.md` | Zero-VRAM Semantic Search | CPU-only FastEmbed embedding runtime preserving 6GB GPU envelope. |
| `references/nemo-guardrails.md` | Formal Safety Rails | Colang 2.x reactive flow rails for input, output, dialog, and loop bounds. |
| `references/ast-grep-py.md` | CST Structural Search | Tree-sitter concrete syntax tree analysis for Python, JS, and HTML. |
| `references/observer-gate.md` | Pre-Commit Structural Gate | Pre-commit structural AST verification and Ruff quality auditing. |
| `references/branch-swapper.md` | MCTS Hypothesis Search | Two-Strike Tabu Monte Carlo Tree Search to prevent dead-end fixation. |
| `references/lora-adapter-manager.md` | Dynamic LoRA Routing | Low-rank adapter routing and hot-swapping under strict VRAM limits. |
| `references/recirculation-adapter.md` | System-2 Recirculation | Prefill loop iteration and Lyapunov convergence metrics for deep reasoning. |
| `references/nora-pipeline.md` | Online Continuous Adaptation | Normalized low-rank adaptation capturing online trajectory buffers. |
| `references/declarative-attention.md` | Attention Allocation | 5-slot context compaction emulating declarative attention masking. |
| `references/graphiti-core.md` | Bi-Temporal Knowledge Graph | Episodic and semantic knowledge graph bridge with temporal invalidation. |
| `references/wmt_concept.md` | Working Memory Time Decay | Decay half-life dynamics and context eviction policies. |

## Procedure

1. **Query Architecture**: Use semantic search via `hermes embed search "<query>"` to locate relevant concept references.
2. **Inspect Reference**: Read the detailed reference file from `references/<concept>.md` on demand.
3. **Verify Compliance**: Run `hermes concepts verify <file>` or `hermes exam` to guarantee contract compliance.

## Pitfalls

- Never load all references simultaneously into working context; load individual references on demand using `skill_view`.
- Never bypass NeMo Colang 2.x rails or Cactus uncertainty gates when executing mutations.

## Verification

Run system examination:
```bash
hermes exam
```
All 118 contract tests must pass with 0 failures.
