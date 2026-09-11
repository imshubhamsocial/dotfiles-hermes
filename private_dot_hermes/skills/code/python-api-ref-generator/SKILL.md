---
name: python-api-ref-generator
description: Generates API reference from Python signatures.
---

# Pipeline: Python API Reference Generator

This skill outlines the DAG for generating an API reference from Python source code.

## Workflow DAG

1.  **File Discovery (Tool Call):**
    *   `hermes_tools.search_files(pattern="*.py", target="files", limit=1000)`: Collect all potential `*.py` source files.
    *   *Constraint:* Filter out non-source files (e.g., `.pyc`, `.db`, `.yaml`, `.json`, `.sh`) to maintain AST integrity.

2.  **Signature Extraction (Code Execution):**
    *   Iterate through filtered files.
    *   `hermes_tools.read_file(path=file_path)`: Ingest file content.
    *   Use `ast.parse` to traverse the code and identify all `ast.FunctionDef` nodes.
    *   Public functions are defined as those whose name does not start with an underscore (`_`).
    *   Collect function name, signature, and docstring.

3.  **Reference Synthesis (Code Execution):**
    *   Aggregate all extracted signatures.
    *   Use `hermes_tools.write_file(path="API_REFERENCE.md", content=markdown_content)` to commit the final document.

## Technical Details

- **Input/Output:** Takes project context; outputs `API_REFERENCE.md`.
- **Core Mechanism:** Leverages AST for robust, syntax-aware signature parsing.