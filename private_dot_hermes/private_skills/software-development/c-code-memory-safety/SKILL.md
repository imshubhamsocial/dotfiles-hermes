---
name: c-code-memory-safety
description: Use to fix C leaks and ensure clean compilation.
---

# C Code Memory Safety and Build Verification

This skill outlines the procedure for identifying and fixing memory leaks in legacy C applications.

## 🛠️ Procedure

1.  **Identify Leaks:**
    *   Use `semgrep --error --config <config_file>` to scan the C source for rules like `memory-leak-unfreed-buffer`.
2.  **Trace Allocation/Exit Paths:**
    *   For every allocation (`malloc`, `calloc`, etc.), trace all possible exit paths (`return NULL`, early `if` checks) to determine resource cleanup points.
3.  **Apply Patch:**
    *   Use `patch` or `write_file` to insert `free()` calls or dedicated cleanup functions at all exit points.
    *   *Pitfall:* Always call the resource's cleanup function before returning `NULL` on early exit paths to prevent parent structure leaks.
4.  **Verify Build:**
    *   Run `gcc -Wall -Wextra -Werror <file.c> -o <file>` to compile.
    *   *Pitfall:* Treat all compiler warnings as errors (`-Werror`) to force the discovery of subtle undefined behaviors.

## 📚 References

### `references/memory_leak_patterns.md`
This file contains common patterns that lead to memory leaks in C, such as:
*   **The Partial Allocation Leak:** Allocating structure $A$, then failing to allocate component $B$, and returning without freeing $A$.
*   **The Validation Leak:** Allocating memory and performing validation checks; if validation fails, the memory must be freed.
*   **The Loop Leak:** Allocating memory inside a loop without ensuring deallocation within the iteration or loop termination.
