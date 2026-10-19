# Phase 20 Invariant Rule: Google Harness² 24/7 Continuous RSI Meta-Loop

## 1. Context & Architectural Grounding
This rule codifies the **Google Harness²** continuous autonomous agent self-improvement standard (arXiv:2610.14224) within the Hermes Agent OS 4-Tier clean architecture. It governs the nightly dream-state meta-loop that inspects operational sessions, extracts failure patterns, and promotes verified behavioral invariants without weight tampering or bespoke runners.

## 2. Mandatory Behavioral Invariants

### Invariant 1: 100% Upstream Native Cron Authority
* All scheduled self-improvement tasks must be scheduled, managed, and executed exclusively through upstream `hermes cron` primitives.
* **Prohibition of Bespoke Runners**: Never create custom Python daemon scripts, cron wrapper files, or background polling loops (e.g. `scripts/harness2_nightly_meta_loop.py`). Continuous execution is handled natively by the Hermes daemon.

### Invariant 2: Zero Test Rule Pollution (Law 3)
* Dream-state evaluation of candidate rules must execute in isolated temporary directories (`tempfile.TemporaryDirectory()`).
* Synthetic or unverified candidate rules must **never** be written directly to `.hermes/rules/` or `~/.hermes/rules/` until fully certified.
* All temporary test rules must be cleaned up immediately upon test conclusion.

### Invariant 3: Regression Guard Verification (Law 6)
* Before promoting any candidate rule to `.hermes/rules/`, Hermes must run the regression test suite across existing testbeds under `tests/`.
* If any regression test fails, the candidate rule is discarded immediately under the Two-Strike Tabu Rule (Law 7).
* Only candidate rules achieving a 100% pass rate (`exit code 0`) and zero performance regression may be committed.

### Invariant 4: Hardware-Bounded Standby & Execution (Law 2)
* The nightly dream loop operates on Port 8138 with **0 MiB permanent VRAM delta**.
* During idle scheduled windows, the GPU remains in low-power standby (P8 state).
* Total active GPU VRAM during dream verification must remain $\le \mathbf{4,812\text{ MiB}}$.

### Invariant 5: Atomic Persistence & Parity Sync
* Promoted rules must follow canonical Markdown naming (`rule_<domain>_<action>.md`).
* All newly promoted rules in `.hermes/rules/` must be synchronized to the Chezmoi dotfiles repository (`~/.local/share/chezmoi/private_dot_hermes/rules/`).
