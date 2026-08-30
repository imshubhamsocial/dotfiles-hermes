# End-to-End Component Flow & Debugging Architecture

This document maps out how every subsystem interacts during a turn, and provides a clear guide for diagnosing what is working, what is failing, or where execution stalls.

---

## 1. End-to-End Execution Pipeline

```
[ User Prompt / Task ]
         │
         ▼
 1. INTENT ROUTING & PROMPT SLOTTING
    ├── Classifies query intent (Code / Chat / Search / Refactor)
    └── 2-Tier Plugin Summary injected (≤ 150 tokens)
         │
         ▼
 2. SUBAGENT & DOMAIN FLEET DISPATCH (Kahn's DAG)
    ├── @architect: Generates spec-first Plan.json
    └── @coder: Synthesizes code diff using Code-Mode SDK
         │
         ▼
 3. JIT TOOL & SKILL ACTIVATION
    ├── FastMCP Server proxies tool call
    └── Web Grounding (SearXNG / ddgs) fetches real data if needed
         │
         ▼
 4. VERIFICATION MATRIX & QUORUM GATE
    ├── Draft Detective: Checks file paths, symbol existence, brace balance
    ├── Cog Verifier: Runs AST syntax checks and local contract test spikes
    └── Quorum Audit Gate: Author != Auditor consensus check (Fitness ≥ 0.85)
         │
         ├──► [REJECTED] ──► 2-Strike Tabu Rule ──► Rollback Git Commit ──► Refine
         │
         ▼ [AGREED]
 5. COMMIT & PERSISTENCE
    ├── VFS & State Checkpoint: SHA-256 tree snapshot committed
    ├── SQLite WAL Experience Store: Episode recorded for offline learning
    └── Return verified receipt to user
```

---

## 2. Debugging Cheatsheet: What to Check When Something Fails

| Symptom | Probable Cause | Where to Look / Diagnostic Command |
|---|---|---|
| **GPU OOM / Process Killed** | Context tokens exceeded physical 6GB limit | Check `context_window_guard.py` and run:<br>`hermes doctor` |
| **Tool Execution Hangs** | Subprocess stuck waiting on stdin or long network call | Check `process_guard.py` (Inactivity timeout = 45s, Max = 300s) |
| **Agent Keeps Repeating Hallucinated File** | Draft Detective gate failed or was bypassed | Run `pytest tests/harness_contracts/test_roadmap4_u55_draft_detective.py` |
| **Changes Refuse to Commit** | Quorum consensus rejected code due to syntax or test drift | Inspect receipt in `.hermes/knowledge/evidence/` or check `quorum_gate.py` |
| **Plugin Not Discovered** | `plugin.yaml` missing or syntax error in manifest | Run `hermes plugins doctor <plugin-name>` |
| **Database Lock / Busy Errors** | SQLite not in WAL mode or concurrent writers blocked | Verify WAL mode: `python3.13 -c "from hermes_core.database import get_state_db_factory; print(get_state_db_factory().is_wal_mode())"` |
| **Search Grounding Fails** | SearXNG container stopped | Start daemon: `podman start searxng-hermes` (or check `web_grounding.py`) |
