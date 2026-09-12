# Behavioral Invariant: Autonomous /loop & Production TUI Protocol
> Inferred from user correction /learn event `evt_autonomous_loop_tui_20260912`

## Mandate
1. **Autonomous `/loop` Execution**:
   - Every prompt task must operate strictly under the autonomous `/loop` methodology.
   - Hermes must autonomously refine the prompt, construct an MRP DAG plan, decompose sub-tasks, explore heavy repositories via symbol indexing and knowledge graphs (`semantic_triples.db`, Graphiti), select and install missing skills or packages dynamically, flush context boundaries at 80% capacity (52,428 tokens) via `/clear`, compact operational cache, and execute independent QA before termination.
2. **Production TUI Standard**:
   - In production and capability benchmarking, Hermes must be invoked using its rich Terminal User Interface (TUI) via `hermes "<prompt>"`.
   - In desktop environments requiring live visual monitoring, launch inside a dedicated terminal emulator:
     `konsole --new-tab -e distrobox enter ws-hermes -- hermes "<prompt>"`
3. **Isolated Evaluation Testbeds**:
   - All prompt-driven capability evaluations under `tests/` must reside in their own dedicated directory with an independent Git repository (`git init .`), guaranteeing total isolation from the parent codebase.
