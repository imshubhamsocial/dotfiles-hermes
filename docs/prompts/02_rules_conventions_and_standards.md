# 02. Rules, Coding Conventions & Cognitive Constraints

> **Authoritative Context**: Master standards and non-negotiable invariant laws for Hermes OS development.

---

## 1. Master Operational Invariants (Cognitive Codebook)

1. **Native Upstream Binary as Single Execution Substrate**:
   * All task execution, live validations, CI pipelines, and agent runs MUST execute through the native upstream binary `hermes -z "<prompt>" --yolo`.
   * **Zero Custom Wrappers**: Never create sidecar runner scripts (e.g. `hermes_os_cli.py`) to bypass upstream behavior or make tests artificially pass. If an upstream run fails, diagnose and fix the root cause in the harness, tool schemas, or system prompts directly.

2. **Full 64K Context Window Guarantee**:
   * The local inference host (`llama-server` on `:8138`) MUST always operate with full `-c 65536` and `--cache-type-k q4_0 --cache-type-v q4_0` enabled.
   * Never reduce context lengths based on assumptions; 64k context fits safely in $\approx 3,745\text{ MiB}$ VRAM.

3. **Zero GPU VRAM Contention for Semantic Search & Tools**:
   * All embedding models (`BAAI/bge-small-en-v1.5` via FastEmbed/ONNX), Tree-sitter AST queries, and schema validators MUST run exclusively on **host CPU / RAMDisk**.
   * GPU compute is strictly reserved for the 4B SLM inference engine.

4. **Kernel-Level Bubblewrap Sandbox & Execution Roots**:
   * Untrusted shell commands MUST execute within `bwrap` namespace jails.
   * Write scratch execution artifacts and compiled binaries to `/tmp` (which supports executable permissions `+x` under rootless containers), while keeping vector databases and state cache on `/dev/shm`.
   * **Trap-1 Error Normalization**: System permission denials MUST be sanitized to a single canonical guidance line to prevent infinite LLM retry loops.

5. **Tool Loop Hard-Stop & 2-Strike Tabu Rule**:
   * Native agent configuration (`~/.hermes/config.yaml`) must enforce `hard_stop_enabled: true` with strict thresholds (`exact_failure: 3`, `same_tool_failure: 4`) to prevent repetitive hallucination loops.

6. **Pre-Commit Observer Gate (Zero-Sorry Ground Truth)**:
   * Never self-grade with conversational claims ("Everything works!").
   * Before committing, verify code through external AST syntax checks, brace balancing, type checking, and Pytest suites.
   * Single-namespace state containment: Generated JS/Python code must encapsulate variables within a single object (e.g. `const APP = {}`) to prevent duplicate declaration collisions.

7. **100% Relative & Portable Paths**:
   * Never hardcode absolute machine usernames or local directories.
   * Resolve paths relative to `$BASH_SOURCE`, `Path(__file__).resolve().parents[...]`, or `$HOME`.

8. **Chezmoi Synchronization Integrity**:
   * Every new architectural file, rule, or launcher modification must be tracked cleanly in Chezmoi (`chezmoi add <path>`).
   * Working tree in Chezmoi should remain clean after completing milestones.

---

## 2. Python & Code Quality Standards

* **Language Standard**: Python 3.13+ with strict type annotations (`from __future__ import annotations`).
* **Test Isolation**: Every contract test in `tests/harness_contracts/` must be completely independent and self-cleaning (use `tmp_path` or `/dev/shm`).
* **Exit Codes**: CLI commands must return exit code `0` on success and non-zero on failure with concise stderr output.
* **Token Economy**: Avoid dumping raw multi-file logs into LLM contexts. Use AST outlines, symbol queries, and line-anchored search-and-replace patches.
