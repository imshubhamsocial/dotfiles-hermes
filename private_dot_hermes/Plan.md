# Plan.md — Active Execution Blueprint

> **Status**: All prior phases (Phases A–G, Part 2 P1/P2 Actions N1–N10, and Horizon 8 Strategic Milestones H8-01–H8-10) are **100% COMPLETE & VERIFIED**.
> **Contract Status**: 271/271 contract tests green. 0 regressions.
> **Current Cycle**: Idle / Ready for Next User Directive.

---

## Active Milestone Queue

| Milestone | Scope | Invariant Boundary | Status |
| :--- | :--- | :--- | :---: |
| *No active pending milestones* | Awaiting new task or experiment specification | Zero-Token Bloat · VRAM ≤ 4,812 MiB | 🟢 READY |

---

## Invariant Directives for Next Session
1. **Spec-First Invariant**: Before emitting code or mutating files, formulate the 4 Director questions and persist milestones into `.hermes/plan.json`.
2. **Loop & Tabu Invariant**: Execute surgical diffs only. Apply the 2-Strike Tabu rule on any failure.
3. **Pre-Commit Verification**: Run observer gate, contract test suite (`make test`), and capability audits before marking completion.
4. **Chezmoi Sync**: Track all configuration, rule, and skill modifications in Chezmoi.
