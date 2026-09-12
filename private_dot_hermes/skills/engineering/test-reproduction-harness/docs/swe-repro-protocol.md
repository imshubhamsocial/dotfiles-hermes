# SWE-agent Reproduction Protocol

1. **Synthesize**: Create `reproduce_issue.py` (or shell equivalent) isolating the failure without editing codebase.
2. **Execute RED**: Confirm the script fails with exit code != 0.
3. **Patch**: Apply minimal surgical edit to the target source.
4. **Execute GREEN**: Confirm `reproduce_issue.py` now exits with 0.
5. **Regression Check**: Run full test suite (`make test` / `pytest`).
