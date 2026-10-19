---
name: phase13-stair-navigation
phase: "Phase 13"
authority: "STAIR Structural AST Navigation"
description: "STAIR ToC/AST structural code retrieval"
---
# STAIR Navigation: Structural Table of Contents & AST Code Retrieval

This skill implements the IBM STAIR (*Structural Table-of-Contents for Code Retrieval*, arXiv:2609.03874) paradigm natively inside Hermes Agent OS.

## 1. Core Principle: Zero Chunk Boundary Slicing
Standard RAG vector indexing breaks code into arbitrary 500-token chunks, often splitting functions across chunk boundaries and discarding class hierarchy context.
STAIR replaces vector chunking with **Deterministic AST Structural Addressing**:
1. Build a Structural Table of Contents (ToC) mapping `File > Class > Method [L_start:L_end]`.
2. Cache the ToC in OpenViking hierarchical memory under `viking://stair/toc_manifest`.
3. Query the ToC to resolve the exact line coordinates of any target symbol.
4. Hydrate the complete, 100% intact function scope using `read_file` with precise line ranges.

## 2. Generating Structural Outlines

### Python, C/C++, TypeScript, Rust, Go:
Execute official `@ast-grep/cli` via `terminal`:
```bash
ast-grep outline <path_to_source_file_or_dir>
```
Output schema:
```text
path/to/module.py
 12: class SessionManager:
       method: __init__, create_session, purge_expired
 45: def standalone_helper(param: str) -> bool:
```

### Markdown Architecture & Spec Files:
For specification documents, extract hierarchical headers:
```bash
grep -nE '^#{1,4} ' <path_to_spec.md>
```

## 3. Storing & Addressing in OpenViking Memory
When onboarding a new repository or subsystem, record the ToC manifest via `viking_remember`:
```bash
# Store under dedicated URI:
viking_remember(uri="viking://stair/toc_manifest", content="<generated_ast_outline_text>")
```

To find symbol definitions across the repository:
```bash
viking_search(query="SessionManager purge_expired line coordinates")
```

## 4. Deterministic Symbol Hydration
Once the line coordinates are resolved (e.g. lines 25 to 60):
* Never read the entire 2,000-line file into context.
* Read precisely the symbol definition:
  ```bash
  read_file(path="path/to/module.py", start_line=25, end_line=60)
  ```
This ensures zero chunk boundary errors, preserves full function signature and docstrings, and saves over 80% context tokens.
