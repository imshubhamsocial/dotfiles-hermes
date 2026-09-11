# BPE Workspace: Belief State

- **OS / Runtime**: Linux / Fedora Distrobox `ws-hermes`
- **Active Phase**: Era 9 Frontier AGI Self-Evolving Superintelligence Harness
- **VRAM Envelope**: Safe (<= 4,800 MiB on RTX 3050 Laptop)
- **Git Tree**: Clean
- **Hardware Policy**: RTX 3050 Laptop Guardrail Enforced
- **Last Updated**: 2026-09-11T11:20:00.000000+00:00

## Session Hypotheses & Invariants
- Zero-token waste: prefix-cache stability > 90%
- Spec-first: verified contracts before mutations
- Continuous verification: 100% test gate passing (245/245)
- Mannered prose elimination: Rule 0 strictly enforced

## Permanent Empirical Invariants
- [hardware] RTX 3050 hardware ceiling: Keep VRAM <= 4,812 MiB to prevent OOM killer. (Internalized, freq: 3)
- [security] Role Security Enforcement: Strict Maker-Verifier isolation (architect=read-only, coder=mutations, tester=execution).
- [evolution] FrogNano Learnability Frontier: Filter training trajectories to [0.3, 0.7] reward boundary for optimal RL learning.
- [harness] Harness Engineering: Preemptive compaction (<2048 budget) and compressed reasoning trace preservation.
- [compute] Embedding compute: Strict CPU-only execution (zero GPU VRAM allocation) to prevent contention with Gemma 4B.
- [architecture] C4 Architecture: Auto-generate Mermaid C4 specs and diagrams from AST symbol index.
- [observability] Trajectory DB: Full recording of every turn, reasoning trace, tool output, and test status into SQLite WAL cache.
- [context] SWE-agent Windowing: Head 25 + Tail 25 line truncation on tool observations exceeding 50 lines.
- [action] Code-as-Action & ACI Diffs: smolagents sandboxed Python scripts and Aider-style unique search-replace diff editing.
- [self-evolution] Meta-Harness Outer Loop: Autonomous failure clustering, patch proposals, and zero-regression test gates with atomic rollback.
- [retrieval] DTDR & A2A: Dynamic tool dependency retrieval via BM25 and typed machine-to-machine Agent Cards.
