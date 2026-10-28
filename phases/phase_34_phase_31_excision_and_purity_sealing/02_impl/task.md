# Implementation Task Checklist: Phase 34

- [ ] Inspect `.hermes/mcp_openjev.py` lines 886–935 (`jev_arc_agi_neurosymbolic_solve`).
- [ ] Remove `jev_arc_agi_neurosymbolic_solve` from `.hermes/mcp_openjev.py` while keeping `mcp.run(transport="stdio")` intact.
- [ ] Update Law 10 in `.hermes/SOUL.md` to POSIX sandbox search-and-verify protocol.
- [ ] Update `phases/phase_31_gemma_cpu_sidecars_neuro_symbolic_arc_agi/03_verify/contract.sh` to assert `assert not hasattr(m, "jev_arc_agi_neurosymbolic_solve")`.
- [ ] Run `ruff check .hermes/mcp_openjev.py` and verify zero linter errors.
- [ ] Execute `phases/phase_34_phase_31_excision_and_purity_sealing/03_verify/contract.sh`.
