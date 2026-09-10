# Hermes Agent OS — Core System Architecture Invariants

§ Invariant 1: Local-First Inference
The system operates exclusively against local llama-server running Gemma 4B at http://127.0.0.1:8138/v1. Zero external cloud LLM APIs, zero cloud webhooks.

§ Invariant 2: Zero External Shell Wrappers
All developer actions, test executions, and verification audits must run through native Hermes commands (`hermes <cmd>`, `/<cmd>`) or lifecycle hooks. Never invoke raw shell scripts or custom makefiles for agent workflows.

§ Invariant 3: Single Canonical Agent Home
All runtime components, configuration, plugins, skills, hooks, and tests reside strictly inside `~/.hermes/`. No dual-hierarchy drift outside this path.

§ Invariant 4: Continuous Verification
System correctness is guaranteed by the native contract test harness (`hermes exam`), maintaining 100% pass across all 118 contract tests in under 10 seconds.
