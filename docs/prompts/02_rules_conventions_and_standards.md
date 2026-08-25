# 02. Rules, Coding Conventions & Cognitive Constraints

> **Authoritative Context**: Master standards and non-negotiable invariant laws for Hermes OS development.

---

## 1. Master Operational Invariants (Cognitive Codebook)

1. **Zero GPU VRAM Contention for Semantic Search & Tools**:
   * All embedding models (`BAAI/bge-small-en-v1.5` via FastEmbed/ONNX), Tree-sitter AST queries, and schema validators MUST run exclusively on **host CPU / RAMDisk**.
   * GPU compute is strictly reserved for the 4B SLM inference engine.

2. **Kernel-Level Bubblewrap Sandbox (`bwrap`)**:
   * Untrusted shell commands MUST execute within `bwrap` namespace jails.
   * Only the active workspace root and `/tmp` are writable mounts. Sensitive host roots (`~/.ssh`, `/etc`, `/var`) are physically absent from the namespace mount table.
   * **Trap-1 Error Normalization**: System permission denials MUST be sanitized to a single canonical guidance line to prevent infinite LLM retry loops.

3. **Pre-Commit Observer Gate (Zero-Sorry Ground Truth)**:
   * Never self-grade with conversational claims ("Everything works!").
   * Before committing, verify code through external AST syntax checks, brace balancing, type checking, and Pytest suites.
   * Single-namespace state containment: Generated JS/Python code must encapsulate variables within a single object (e.g. `const APP = {}`) to prevent duplicate declaration collisions.

4. **100% Relative & Portable Paths**:
   * Never hardcode absolute machine usernames or local directories.
   * Resolve paths relative to `$BASH_SOURCE`, `Path(__file__).resolve().parents[...]`, or `$HOME`.

5. **Chezmoi Synchronization Integrity**:
   * Every new architectural file or rule must be tracked cleanly in Chezmoi (`chezmoi add <path>`).
   * Working tree in Chezmoi should remain clean after completing milestones.

---

## 2. Python & Code Quality Standards

* **Language Standard**: Python 3.13+ with strict type annotations (`from __future__ import annotations`).
* **Test Isolation**: Every contract test in `tests/harness_contracts/` must be completely independent and self-cleaning (use `tmp_path` or `/dev/shm`).
* **Exit Codes**: CLI commands must return exit code `0` on success and non-zero on failure with concise stderr output.
* **Token Economy**: Avoid dumping raw multi-file logs into LLM contexts. Use AST outlines, symbol queries, and line-anchored search-and-replace patches.
