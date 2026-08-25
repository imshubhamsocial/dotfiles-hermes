# Agent Milestones — Part 3 of 3: Gaps & Next Steps

> **Read order**: You are reading file **3/3**.
> Prev → [`AGENT_OPERATIONS.md`](./AGENT_OPERATIONS.md) (how to run hermes)
> Start → [`AGENT_CONTEXT.md`](./AGENT_CONTEXT.md) (environment & migration state)

---

## Migration Fixes Completed (2026-08-25)

The following issues were identified and fixed during migration verification:

1. ✅ **AGENT_CONTEXT.md** — Corrected model from `qwen3.8-4b:latest` to `gemma-4-4b`, port from `11434` to `8138`
2. ✅ **config.yaml** — Updated model default and base_url to match actual running configuration
3. ✅ **chezmoi config.yaml** — Synced with main config
4. ✅ **AGENT_OPERATIONS.md** — Updated model examples
5. ✅ **context_length_cache.yaml** — Updated model reference
6. ✅ **SOUL.md** — Replaced all `ws-ai` references with `ws-hermes`, removed `distrobox enter` prefixes
7. ✅ **frontier-lean/config.yaml** — Removed old `LLMs/Cluster` path, now uses `~/.hermes/skills`
8. ✅ **e20smoke skills** — Removed hardcoded `LLMs/Cluster` paths from skill templates
9. ✅ **Various skills** — Updated `distrobox enter ws-ai` commands to direct execution
10. ✅ **aquarium-benchmark skill** — Removed old path references

---

## Known Gaps (What Still Needs Work)

These items were identified by Antigravity but not yet completed:

1. **MCP Servers** — `~/.hermes/plugins/` is tracked by chezmoi but currently empty. MCP server configs/launchers need to be added and tested.

2. **Hermes update** — Hermes reports `Update available — run 'hermes update'`. Decide whether to update to latest or stay pinned at `v0.20.4`. If updating, re-verify all configs.

3. **llama-server GPU test** — The patched `llama-server` wrapper is in place but hasn't been tested end-to-end with a GGUF model on the RTX 3050. Test with a small GGUF model.

4. **Hooks** — `~/.hermes/hooks/` is tracked by chezmoi but empty. Implement any required lifecycle hooks.

5. **fastembed/BGE model pull** — `~/.cache/fastembed/` only has an `xet` directory. No BGE model has been downloaded yet. Pull with `fastembed pull BAAI/bge-small-en-v1.5` or equivalent.

6. **setup.sh completeness** — `setup.sh` currently doesn't include: hermes binary installation (git clone + editable install), BGE model pull, or MCP server setup. Add these for full reproducibility.

7. **`clearfront` version conflict** — `clearfront==2.7.3` requires `rich>=15.0.0` but `rich==14.3.3` is installed. Resolve if `clearfront` is needed.

---

## Prioritized Next Steps (Suggested Order)

1. Fix `setup.sh` to be fully reproducible end-to-end (hermes git install, BGE pull, MCP stubs)
2. Test `llama-server` with a GGUF model on GPU
3. Set up MCP server configs in `~/.hermes/plugins/`
4. Pull BGE/fastembed models
5. Review hermes update decision
6. Resolve `clearfront` rich version conflict
7. Commit all changes to chezmoi

---

> After completing milestones, commit everything:
> ```bash
> # From inside ws-hermes
> chezmoi add ~/.hermes/plugins/ ~/.hermes/hooks/
> chezmoi git -- commit -m "Add MCP configs, hooks, and updated setup.sh"
> ```
