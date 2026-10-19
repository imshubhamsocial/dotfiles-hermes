---
phase: "Phase 01"
authority: "Zero Bespoke Python Debt Mandate"
testbed: "tests/"
status: "Operational & Certified"
---

# Architectural Invariant: Zero Bespoke Files

This invariant mandates that the Hermes Agent OS operates exclusively through upstream-sanctioned extension mechanisms and validated components. Any custom or unverified code within `~/.hermes/` must be documented, justified, and integrated into the official Hermes framework before being considered valid.

## Operational Constraints

1.  **Extension Mechanisms:** All extended capabilities must leverage approved mechanisms:
    *   **MCP Servers:** Defined and managed via `config.yaml` in the designated `mcp_servers` section.
    *   **Skills:** Must reside in `~/.hermes/skills/` and adhere to a trigger description strictly less than 40 characters.
    *   **Memory Plugins:** Must be officially recognized and bundled within `~/.hermes/memories/`.

2.  **Bespoke File Prohibition:** The directory `~/.hermes/` must remain free of the following unverified assets:
    *   Standalone Python scripts not registered as skills or plugins.
    *   Mock specifications (`*.spec.md` outside of officially sanctioned project specs).
    *   Fake or unverified GGUF model stubs or configuration files.
    *   Unverified or unauthorized cron jobs not documented in `~/.hermes/cron/`.

3.  **Verification:** Adherence to this invariant is verified via `hermes doctor` and mandatory checks against `~/.hermes/rules/canonical_upstream_parity.md`.