# Invariant Rule: STAIR Structural AST Navigation & Hierarchical Code Addressing

## 1. Context & Motivation
Lightweight models (such as Gemma-4-E4B) easily get context-saturated when dumping full multi-thousand-line source files into context or when vector chunking slices functions across chunk boundaries.
Per IBM STAIR (arXiv:2609.03874) and Anthropic 5-Layer Memory, code navigation must proceed structurally from hierarchical Table of Contents (ToC) to exact line hydration.

## 2. Mandatory Operational Invariants

### Invariant 1: Structural AST Outline Before Whole-File Dumps
When exploring or locating functionality in codebases with multiple modules:
- **PROHIBITED**: Reading whole source files (>150 lines) into context without knowing the exact target symbol.
- **MANDATORY**: Run `ast-grep outline <path>` first to inspect the class and method structure.

### Invariant 2: Zero Chunk Slicing (Coordinate Hydration)
- When inspecting a specific method, extract its starting and ending line bounds from `ast-grep outline` or grep line ranges.
- Use `read_file` with `start_line` and `end_line` bounds to read the 100% complete, intact function scope.
- Never rely on arbitrary token chunk boundaries that bisect function signatures or loop blocks.

### Invariant 3: Memory Manifesting in OpenViking
- In large repositories or persistent projects, persist discovered module ToCs to OpenViking memory under `viking://stair/toc_manifest` via `viking_remember`.
- Query `viking_search` to recall previously indexed symbol coordinates across sessions.
