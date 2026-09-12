# Clean-Slate Regeneration Math (arXiv:2609.05364)

Incremental patching accumulates generation debt:
$$D_{t+1} = \lVert G(S_{t+1}, C_t) - G(S_{t+1}) \rVert > 0$$

SMART clean-slate rebuild regenerates the module directly from design docs:
$$C_{t+1} = G(S_{t+1}) \implies D_{t+1} = 0$$

Always maintain worked examples and SymPy closed-form reconciliation anchors.
