# Phase 08: Autonomous Headless & Konsole TUI Execution — Implementation Checklist

> **Phase Directory**: `phase_08_autonomous_headless_konsole_tui_execution`  
> **Status**: Stage `02_impl` execution complete  

---

## 1. Targeted Symbols & Code Modules
- Target File(s):
  - Environment IPC: `TMPDIR="/tmp"` short-path socket constraint
  - CLI Health: `hermes doctor` diagnostic suite
- Module Stems:
  - POSIX `UNIX_PATH_MAX` IPC socket bounds & Hermes runtime diagnostics
- Required Skills:
  - `karpathy-surgical-diff`

---

## 2. Causal Hypotheses
1. Default long nested paths can exceed POSIX `UNIX_PATH_MAX` (108 bytes) when binding AF_UNIX IPC sockets during headless or TUI tool execution. Restricting `TMPDIR` to `"/tmp"` bounds socket paths to <= 48 bytes.
2. Executing `hermes doctor` deterministically audits configuration purity, SQLite state DB, memory providers, and CLI availability without consuming GPU VRAM.

---

## 3. Surgical Implementation Plan
- [x] Step 1: Formulate single-cause causal hypothesis.
- [x] Step 2: Ensure non-git backup exists (`<target>.hermes.bak`) if mutating Domain B files.
- [x] Step 3: Verify `TMPDIR` environment length constraint (`len(TMPDIR) <= 16`).
- [x] Step 4: Run `hermes doctor` diagnostic verification exiting 0.
- [x] Step 5: Advance stage to `03_verify` in `03_verify/status.json`.
