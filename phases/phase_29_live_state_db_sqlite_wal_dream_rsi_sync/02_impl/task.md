# Phase 29: Live state.db SQLite WAL Dream-RSI Sync — Implementation Checklist

> **Phase Directory**: `phase_29_live_state_db_sqlite_wal_dream_rsi_sync`  
> **Status**: Ready for Stage `02_impl` execution  

---

## 1. Targeted Symbols & Code Modules
- Target File(s): `tests/phase29_live_dream_rsi_eval/scenario/live_sync.py`
- Target Symbol: `LiveDreamSyncEngine.build_tree_dict`
- Module Stems: `live_sync`
- Required Skills: `karpathy-surgical-diff`, `viking-retrieval`

---

## 2. Surgical Implementation Plan
- [x] Step 1: Formulate single-cause causal hypothesis:
  - **Hypothesis**: In `LiveDreamSyncEngine.build_tree_dict`, `title = sess[5]` directly indexes index 5 of a 5-element session tuple `(id, source, model, started_at, completed_at)`, raising `IndexError: tuple index out of range`. Accessing `title = sess[1]` maps the session title/source safely.
- [x] Step 2: Ensure non-git backup exists (`<target>.hermes.bak`) if mutating Domain B files (Target is in Domain C git repository).
- [ ] Step 3: Apply mutation via `jev_mutate_module` adhering to Karpathy U12 15-line diff limit.
- [ ] Step 4: Verify pre-commit `ast.parse` and post-write `ruff check` pass with code 0.
- [ ] Step 5: Advance stage to `03_verify` in `03_verify/status.json`.
