---
name: undolist-logic-fix
description: "Fix undo list entries for zero-width changes in C."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [debugging, undo, undolist, c-code, buffer-api, state-management]
    related_skills: [systematic-debugging]
---

# Undolist Logic Fix

This skill documents the workflow for preventing unnecessary undo entries caused by zero-width changes.

## Procedure

1.  **Identify Symptom:** An undo history entry is created despite no character change (e.g., mode switching).
2.  **Trace Execution:** Break on the core save function (`u_savecommon` in `undo.c`) to observe the arguments (`top`, `bot`).
3.  **Determine Change Width:** Calculate `size = bot - top - 1`.
4.  **Apply Guard:** If `size <= 0`, the change is structural, not a data modification. The fix is to add an explicit guard in the save function:
    *   `if (size <= 0) { return OK; }`
5.  **Verify:** Run the build (`ninja`) and the reproduction script (`repro_undolist.sh`).
6.  **Final Verification:** Ensure the overall build remains stable.

## Pitfalls

- **Zero-Width Fix:** When modifying C functions like `u_savecommon`, only add the zero-width check. Do not refactor surrounding logic unless the compiler explicitly demands it, as this risks breaking existing, valid undo behavior.
---

# Undolist Reference Guide

## u_savecommon Analysis

### Zero-Width Change Pitfall
The undo system saves state changes between `top` and `bot`. If `bot - top - 1 <= 0`, no characters were inserted or deleted. The bug manifests when the API calls `u_savecommon` with a zero-width change, causing a superfluous entry.
```c
// Path: ./neovim/src/nvim/undo.c
// Fixed logic:
//   linenr_T size = bot - top - 1;
//   if (size <= 0) {
//     return OK;
//   }
```