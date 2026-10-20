# Phase 26 Rule: Zero-Spoon-Feeding Turn-1 Intent Compilation Invariant

> **Tier**: 1 Source Ledger (Compiled into SOUL.md Pillar 1 & AGENTS.md Law 12)  
> **Theoretical Grounding**: Gemma-4-E4B SWA Attention Physics, Google Harness² 8-Tuple Decomposition (arXiv:2610.14224), ADR-4, ADR-13  
> **Hardware Budget**: 100% CPU RAM, $\Delta \text{CUDA VRAM} \equiv 0.0\text{ MiB}$

---

## 1. Zero-Spoon-Feeding Operational Law
1. **Unstructured Human Input Authority**:
   Human operators interact with Hermes exclusively through natural-language prompts. The agent MUST NOT demand, require, or wait for manual `/goal` blocks, `outcome:` declarations, `verify:` command strings, or negative constraint boundaries.
2. **Turn-1 Automatic Compilation**:
   Under `<global>` declarative attention, the agent's first action on receiving an un-spoon-fed prompt is invoking `mcp_openjev(jev_compile_intent, raw_prompt=q, workspace_dir=cwd)`.
3. **Execution Manifest Invariant**:
   The compiler runs on CPU RAM in <35 ms with `CUDA_VISIBLE_DEVICES=""`, outputting:
   - Sanitized AST symbol outlines (`L<start>-L<end>`).
   - Inferred verification command ($V_{\text{contract}}$).
   - Recommended JIT Layer 4 skills.
   - Pinned negative constraints (NC-001: No concurrent PyTorch, NC-002: No multiline sed/awk, NC-003: Karpathy U12 $\le 15$ lines).
4. **Attention Transition**:
   Upon receipt of the Execution Manifest in the active SWA tail, the agent immediately transitions to `<focus id="<target_symbol>">`, hydrates the recommended skill via `skill_view`, and proceeds with surgical implementation.
5. **Machine-to-Machine Schema Boundaries**:
   Explicit `/goal` schemas are strictly reserved for machine-to-machine automation:
   - Automated cron daemons in `.hermes/cron/jobs.json`.
   - Continuous integration benchmark harnesses (`run_eval.sh`).
   - Internal AST cognitive manifests.
