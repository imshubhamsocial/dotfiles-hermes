# rule_dream_rsi_meta_loop.md — Invariant Operating Rule for Offline Replay & MASS-RRSI Meta-Evolution

> **Target**: Hermes Agent OS & Recursive Self-Improvement Runtime  
> **Authority**: Phase 16 Architectural Standard (`Evolution.md` Section 3.5 & 4.1)  
> **Theoretical Grounding**: Google/DeepMind Dream-RSI (*arXiv:2609.14858*), Sakana AI MASS (*arXiv:2610.12176*), Google RRSI (*arXiv:2609.24972*)

---

## 1. Context & Architectural Mandate

During idle or post-task periods, Hermes evolves its Layer 4 skills, operational prompts, and heuristics via an offline background meta-loop. To prevent catastrophic overfitting to recent tasks, Out-of-Distribution (OOD) performance regression, and excessive token waste, the agent OS must enforce three structural invariants:

1. **Disk-Based World Replay Simulator ("Dreaming")**:
   - Rather than executing live GPU inference or real compilations to test counterfactual branch orderings, historical execution traces (`telemetry/traces.jsonl`) are modeled as cached directed acyclic graphs (DAGs) on disk: `.hermes/cache/dream_worlds/<task_hash>.json`.
   - Node attributes must record: `(state_hash, focus_regime, tool_name, diff_lines, attended_tokens, duration_ms, pytest_exit_code)`.
   - Counterfactual branch search ("Dreaming") simulates alternative tool pivot sequences and Two-Strike rollbacks in memory, achieving $\ge 1.40\times$ call reduction without live inference calls.

2. **Sequential MASS 3-Pass Role Switching on Port 8138**:
   - To achieve Society-of-Mind collective intelligence without multiplying VRAM allocations, the offline worker executes three strictly sequential passes on the single-slot (`-np 1`) Port 8138 `llama-server`:
     - **Pass A (Failure & Branch Analyst)**: Audits traces for dead-end tool calls, unpruned context saturation, and repeated diff thrashing.
     - **Pass B (DSPy/GEPA Harness Evolver)**: Synthesizes mutated Layer 4 skills (`~/.hermes/skills/*/SKILL.md`) and spoke contracts (`AGENTS.md`) with strictly $\le 40$-character frontmatter descriptions.
     - **Pass C (RRSI Leakage & Contradiction Critic)**: Audits proposed mutations and rejects any patch containing hardcoded test literals, testbed path references (`tests/*_eval/`), or contradictions against `MEMORY.md` and `EXPERIENCE.md`.

3. **RRSI Stability Acceptance Gate**:
   - A candidate mutated harness $H'$ is committed to `~/.hermes/` and Chezmoi if and only if its empirical performance improvement across validation benchmarks exceeds the baseline noise margin:
     $$\mu(H') - s^* \ge k \cdot \sigma_0$$
     where $\sigma_0$ is the empirical noise standard deviation of baseline evaluations and $k \ge 1.0$.
   - Held-out verification suites must exit 0 with 0 test regressions.
