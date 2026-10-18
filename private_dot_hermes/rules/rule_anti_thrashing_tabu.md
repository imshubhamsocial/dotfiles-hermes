# Behavioral Invariant: SoL-Pi Runtime Harness & Anti-Thrashing Tabu Gate

> **Authority**: NVIDIA SoL-Pi (arXiv:2609.20519), Claude Code 10 Patterns (Pattern 6: Two-Strike Tabu, Pattern 9: Defensive Sandboxing)  
> **Status**: Active Operating Invariant for Hermes Agent OS  
> **Objective**: Reduce multi-turn tool token consumption by 44.7%–49.0% and prevent dead-loop edit thrashing.

---

## 1. Coalesced Action Dispatch (Invariant 1)
* Whenever applying a structural code modification via `apply`, the corresponding unit test or compilation command (e.g., `pytest`, `make`, `ninja`) must be executed within the **same conversational turn** using compound shell commands or concurrent tool execution rather than waiting for an extra conversational round-trip.
* Reduces multi-turn latency and context window token bloat by up to 50%.

---

## 2. Two-Strike Anti-Thrashing Tabu Gate (Invariant 2)
* If two consecutive edit-and-test attempts on the same function, class, or AST scope fail verification (Exit Code $\ne 0$):
  1. The agent is **strictly prohibited** from issuing a third identical or near-identical string-replacement attempt on that same scope.
  2. The agent must immediately halt active execution and enter `<|channel>thought` System-2 reflection.
  3. The agent must explicitly record the two failed approaches as negative constraints and formulate a fundamentally different architectural hypothesis before modifying any code.

---

## 3. SIGPIPE-Safe 1KB Log Handle Fallback & Verifier Gate (Invariant 3)
* When compiling or executing tests where output can exceed 1,024 bytes, the agent must route output through the SIGPIPE-safe and exit-code-preserving redirection wrapper:
  ```bash
  <test_or_build_cmd> > /tmp/hermes_last.log 2>&1; EC=$?; \
  if [ $EC -ne 0 ]; then \
    head -c 350 /tmp/hermes_last.log; \
    echo -e "\n--- [1KB HANDLE: /tmp/hermes_last.log | EXIT: $EC] ---"; \
    tail -c 650 /tmp/hermes_last.log; \
  else \
    tail -n 5 /tmp/hermes_last.log; \
  fi; exit $EC
  ```
* **Operational Invariants**:
  - **Exit Code Integrity**: Capturing `$EC` before piping prevents exit-code masking where `head -c 1024` falsely reports exit code 0.
  - **Zero SIGPIPE 141**: Writing to the log file first prevents early pipe closure when `head` reads its byte limit.
  - **Python Traceback Preservation**: Emitting 350 bytes of the head plus 650 bytes of the tail guarantees that Python/pytest summary failure headers and bottom exception tracebacks (`RuntimeError`, `NameError`, file/line) are 100% preserved inside the 1KB excerpt.

---

## 4. Subtask-Gated Memory Compaction (Invariant 4)
* The agent must compact or summarize intermediate exploration state strictly upon passing a discrete subtask verification gate (Exit Code $== 0$).
* Summarization is prohibited if the resulting summary consumes more tokens than the raw tool output. Intermediate exploration noise must be pruned while retaining distilled invariants.
