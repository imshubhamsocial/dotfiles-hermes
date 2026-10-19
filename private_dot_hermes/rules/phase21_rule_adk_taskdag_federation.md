# Phase 21 Invariant: Google ADK 2.9+ Multi-Agent TaskDAG & A2A Federation

> **Authority**: Google Agent Development Kit (ADK 2.9.0), Agent2Agent (A2A) Protocol (JSON-RPC 2.0)  
> **Status**: Certified Operational Invariant (Phase 21)  
> **Hardware Boundary**: 0 MiB CUDA VRAM Delta (Shared Port 8138 Slot, 100% CPU Routing)

---

## 1. Multi-Agent TaskDAG Graph Topologies

1. **Deterministic DAG Scheduling**:
   - Complex multi-turn software engineering tasks must never execute as unstructured, monolithic chat loops.
   - Goals are decomposed into a Directed Acyclic Graph (DAG) $\mathcal{G}_{\text{task}} = (\mathcal{V}, \mathcal{E})$, where vertices $v_i \in \mathcal{V}$ represent distinct operational subtasks and directed edges $(v_i, v_j) \in \mathcal{E}$ define strict execution prerequisites.
   - Scheduling must be determined via Kahn's algorithm or depth-first search with explicit cycle detection. Any circular dependency must halt execution immediately.

2. **Strict Persona Sandbox Isolation**:
   Every vertex $v_i$ is bound to a single, sandboxed persona subagent $\pi_i$ with strict capability boundaries:
   - **`@architect`**: Read-only AST symbol mapper and contract designer.
     * Allowed: `read_file`, `ast_grep_outline`, `inspect_symbols`, `analyze_spec`.
     * Forbidden: File mutations (`apply_patch`, `write_to_file`) and verification test execution.
   - **`@coder`**: Surgical implementation specialist.
     * Allowed: `apply_patch`, `edit_file`, `surgical_replace`.
     * Forbidden: Running compilers/pytest or authoring high-level contracts. Must respect Karpathy U12 ($\le 3\times$ line diff bound).
   - **`@tester`**: Independent compiler and pytest verification validator.
     * Allowed: `run_pytest`, `run_compiler`, `run_linter`.
     * Forbidden: Modifying application source code.
   - **`@critic`**: Trajectory scoring and Harness² evaluator.
     * Allowed: `evaluate_trajectory`, `compute_reward`, `verify_receipt`.
     * Forbidden: Tool executions outside metric scoring and epistemic receipt verification.

---

## 2. Zero-Context-Pollution A2A Transfers

1. **Typed JSON-RPC 2.0 Messages**:
   - Inter-agent communication is governed strictly by the `transfer_to_agent` RPC method:
     ```json
     {
       "jsonrpc": "2.0",
       "method": "transfer_to_agent",
       "params": {
         "sender": "@architect",
         "recipient": "@coder",
         "task_id": "step_1",
         "structured_payload": { ... },
         "raw_logs_pruned": true
       }
     }
     ```
2. **Log Flood Stripping Invariant**:
   - Raw terminal logs, verbose stack traces, and intermediate scratchpad states must be stripped before emitting transfers.
   - Recipient context windows receive only compact structured payloads ($\le 300$ tokens), guaranteeing `context_pollution_tokens == 0`.

---

## 3. Hardware Boundary & Epistemic Receipts

1. **Zero CUDA VRAM Delta**:
   - Multi-agent TaskDAG scheduling and A2A event routing execute 100% on CPU RAM.
   - Subagents share the single Port 8138 inference slot sequentially without spawning concurrent LLM server processes, preserving the strict 4,812 MiB VRAM ceiling.
2. **Epistemic Receipt Closure**:
   - A multi-agent DAG task reaches deterministic epistemic closure if and only if `@tester` executes the canonical verification command, returning exit code 0 and sealing `/tmp/hermes_verified_receipt.json`.
