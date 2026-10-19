---
phase: "Phase 09"
authority: "Autonomous /loop & Production TUI Protocol"
testbed: "tests/"
status: "Operational & Certified"
---

# Behavioral Invariant: Autonomous /loop & Production TUI Protocol
> Inferred from user correction /learn event `evt_autonomous_loop_tui_20260912`

## Mandate
1. **Autonomous `/goal` & `/loop` Synergy (Golden Law 12)**:
   - Every prompt task must operate strictly under the autonomous `/goal` contract coupled with the `/loop` iterative self-correction harness.
   - Prompts must adhere to the community standard schema:
     ```text
     /goal <Objective>
     outcome: <Expected machine-verifiable end state>
     verify: <Executable assertion command exiting 0>
     constraints: <Surgical diff bounds, 2-strike tabu rule, zero root pollution>
     boundaries: <Confined filesystem directories>
     ```
   - Casual, unstructured, single-turn prompts are strictly prohibited. The agent must not halt until `verify` passes.
   - Every successful resolution must conclude with `/loop learn` (or interactive `/learn`) to distill verified invariants and build recipes into `.hermes/rules/`.
2. **Autonomous `/loop` Execution**:
   - Hermes must autonomously refine the prompt, construct an MRP DAG plan, decompose sub-tasks, explore heavy repositories via symbol indexing and knowledge graphs (`semantic_triples.db`, Graphiti), select and install missing skills or packages dynamically, proactively compress context at 87% effective token budget (~48,000 tokens) before attention degradation, keeping the prefix cache strictly byte-static across turns, and execute independent QA before termination.
3. **Production TUI Standard**:
   - In production and capability benchmarking, Hermes must be invoked using its rich Terminal User Interface (TUI) via `hermes "<prompt>"`.
   - In desktop environments requiring live visual monitoring, launch inside a dedicated terminal emulator:
     `konsole --separate -e distrobox enter ws-hermes -- hermes "<prompt>"`
4. **Isolated Evaluation Testbeds**:
   - All prompt-driven capability evaluations under `tests/` must reside in their own dedicated directory with an independent Git repository (`git init .`), guaranteeing total isolation from the parent codebase.

