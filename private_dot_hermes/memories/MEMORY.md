# Hermes Agent OS — Core System Architecture Invariants

§ Invariant 1: Local-First Inference & Hardware Envelope
The system operates exclusively against local llama-server running Gemma 4B / Qwen 7B at http://127.0.0.1:8138/v1. Hardware envelope is strictly bounded to NVIDIA RTX 3050 Laptop <= 4,800 MiB VRAM. Embeddings run CPU-only. Zero cloud LLM APIs, zero cloud webhooks.

§ Invariant 2: Zero External Shell Wrappers & Single Canonical Entry Point
All developer actions, test executions, and verification audits run exclusively through native Hermes commands (`hermes <cmd>`, `/<cmd>`) or lifecycle hooks. Never invoke raw shell scripts or custom makefiles for agent workflows.

§ Invariant 3: Single Canonical Agent Home
All runtime components, configuration, plugins, skills, hooks, and tests reside strictly inside `~/.hermes/`. Project and host paths remain synchronized with zero drift.

§ Invariant 4: Continuous Verification Gate
System correctness is guaranteed by the native contract test harness (`hermes exam`), maintaining 100% pass across all 220+ contract tests in under 15 seconds.

§ Invariant 5: Belief-Progress-Experience (BPE) State Integrity
Every session adheres to the BPE memory model (belief.md for environmental facts, progress.md for subgoal DAGs, experience.db for empirical insights).

§ Invariant 6: Cryptographic Audit Trail & Security Boundary
All filesystem mutations, role security checks (@architect, @coder, @tester), and Shannon entropy validations are chained into an append-only SHA256 cryptographic audit ledger.
