---
name: substrate-integrity-audit
description: Audit substrate for zero bespoke files.
---

# Substrate Integrity Audit

This skill performs an integrity check on the local Hermes substrate to ensure compliance with the Zero-Bespoke-Files Invariant.

## Audit Steps

1.  **Verify Foundational Files:** Check for the presence and integrity of core rules and binaries within `~/.hermes/`.
2.  **Search for Bespoke Scripts:** Systematically scan `~/.hermes/` for unverified files including standalone scripts, mock specs, fake GGUF stubs, or unauthorized cron jobs.
3.  **Invariant Validation:** Check for the existence and content of `rule_zero_bespoke_files_invariant.md` to confirm architectural mandates are codified.
4.  **Report Compliance:** Output a status report detailing the findings and compliance level.

## Constraints

*   Must only use upstream-sanctioned mechanisms (Skills, MCP, Bundled Memory).
*   Prohibits bespoke, unverified, or unauthorized assets.
*   Operates strictly within `~/.hermes/` directory.