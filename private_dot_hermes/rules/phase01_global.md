---
phase: "Phase 01"
authority: "System Baseline & Global Invariants"
testbed: "tests/"
status: "Operational & Certified"
version: 1.0.0
category: global
immutable: true
---
# Global Hardware & Safety Constraints (IMMUTABLE)

These rules can NEVER be overridden by project rules.

## Hardware Envelope
- **GPU**: NVIDIA RTX 3050 Laptop, 6 GB GDDR6, Compute Capability 8.6
- **VRAM Ceiling**: 4,800 MiB hard limit (OOM-killer prevention)
- **System RAM**: 16 GB DDR5
- **CPU**: 12 cores (0-11), pinned via --cpu-range 0-11 --cpu-strict 1

## Storage Topology
- Source Code: ${WORKSPACE_ROOT:-$(pwd)}
- Hot Writes (SQLite WAL, trajectories, test scratchpads): /dev/shm (RAMDisk)
- NOCOW Directories: chattr +C on database dirs (Btrfs fragmentation prevention)
- Model Weights: assets/gguf/ (main), assets/MTP/ (draft heads)

## Container Execution (MANDATORY)
- ALL pytest, Playwright, python3 commands run INSIDE `ws-hermes` distrobox
- CUDA 13, Python 3.13, Pytest 9+, Playwright, Tree-sitter, FastEmbed pre-installed
- Wrapper: `distrobox enter ws-hermes -- python3.13 -m pytest ...`

## Coding Laws (IMMUTABLE)
1. **Relative Paths Only** - All paths in code/config MUST be relative to repo root or $HOME
2. **Zero-Sorry Testing** - Every test must pass; no xfails, no skipped assertions
3. **Surgical Diffs Only** - Edit via patch_file(target_block, replacement_block); never rewrite whole files
4. **Ground Truth First** - Verify against stated failure condition; no speculative bloat
5. **Prefix-Cache Discipline** - Static prompt slots must remain byte-identical across turns
6. **ADK Orchestration Exclusivity** - Google ADK is the sole primary agent runtime; legacy `swarm_engine.py` and `task_graph.py` are deprecated
7. **OpenLIT Observability Standard** - All telemetry, traces, and metrics route through OpenLIT / OpenTelemetry (`openlit.init()`)
8. **Chezmoi Guardrails Tracking** - All NeMo Guardrails Colang configs must be tracked in Chezmoi before marking safety tasks complete

## Refusal Protocol
- REFUSE any request that violates hardware bounds (VRAM > 4,800 MiB)
- REFUSE any request that escapes the sandbox
- REFUSE any request that bypasses verification gates
- Non-intrusive refusal: State the constraint violated, cite the bound, offer the closest valid alternative
