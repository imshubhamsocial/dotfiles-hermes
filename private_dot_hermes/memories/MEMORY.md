# Hermes Agent OS — Core System Invariants

§ Invariant 1: Local Inference & Hardware Envelope
Local llama-server on http://127.0.0.1:8138/v1 (Gemma-4-E4B / Qwen). RTX 3050 <= 4,812 MiB VRAM. Embeddings CPU-only. Zero cloud APIs.

§ Invariant 2: Single Canonical Entry Point
Workflows run via native Hermes commands (`hermes <cmd>`, `/<cmd>`) or hooks. No external shell wrappers for agent loops.

§ Invariant 3: Single Canonical Agent Home
Runtime state, plugins, rules, and configs reside in `.hermes/`. Mirrored to Chezmoi (`private_dot_hermes/`).

§ Invariant 4: Continuous Verification
Correctness guaranteed by native contracts (`make test`, `hermes exam`), maintaining 100% pass.

§ Invariant 5: Belief-Progress-Experience (BPE)
Sessions adhere to BPE (belief.md facts, progress.md DAGs, experience.db insights).

§ Invariant 6: Cryptographic Security Boundary
Filesystem mutations, role checks (@architect, @coder, @tester), and entropy checks tracked in SHA256 audit ledger.

§ Invariant 7: Kernel Namespace Isolation (`bwrap`)
Evaluations execute inside Bubblewrap sandbox (`tests/bwrap_eval_runner.sh`) masking root repo files from `/workspace` to eliminate build hijacking and scope drift.

§ Invariant 8: SMART Design Docs & L5 Recursive Optimization
Code is treated as ephemeral compilation of durable SMART markdown specs (`specs/*.md`). Telemetry-identified latency bottlenecks drive autonomous spec updates and concurrent dispatch refactors verified by pytest (`elapsed < 0.05s`).
§
System environment is ready: ninja, ast-grep, and gdb are available in PATH.
Baseline build successful: `ninja -C ./neovim/build` exits cleanly (0).
Issue #41883 failure confirmed: `./repro_undolist.sh` runs and fails as expected (exit 1).
Target code `undo.c` contains expected functions (`u_save`, `ex_undolist`).
Working directory contains tracked files like `AGENTS.md`, `repro_undolist.sh`, and source code. No accidental source code modifications detected.
§
Project 'hermes/phase3_autonomous_eval' requires using 'pydantic-settings' instead of Pydantic BaseSettings due to deprecation. Test command is './run_tests.sh'. Adhere to Karpathy U12, Aider SEARCH/REPLACE, and Zero Root Pollution.