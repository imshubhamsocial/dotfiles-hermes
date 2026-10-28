# Phase 34 Specification: Codebase Excision & Substrate Purity Sealing

## 1. Objective
Permanently excise the Potemkin mock solver `jev_arc_agi_neurosymbolic_solve` from `.hermes/mcp_openjev.py`, purge mock references in Law 10 of `.hermes/SOUL.md`, and realign `phases/phase_31_.../03_verify/contract.sh` to seal repository purity.

## 2. Invariants
- `git diff .hermes/mcp_openjev.py` must show the deletion of lines 886–935 with 0 syntax errors (`ruff check .hermes/` and `python3 -m py_compile`).
- `grep -rn "jev_arc_agi_neurosymbolic_solve" .hermes/` must return exit code 1 (0 matches).
- FastMCP server entrypoint `mcp.run(transport="stdio")` must remain functional.
- Receipt `/tmp/hermes_verified_receipt.json` must be written with `exitstatus == 0`.
