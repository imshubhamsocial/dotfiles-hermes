---
name: icm-architect
description: "Jake Van Clief's Interpretable Context Methodology (ICM / MWP) Workspace Architect & Schema Validator. Enforces 5-Layer Progressive Hierarchy (Layers 0-4), 80-line CONTEXT.md caps, 200-line reference caps, 4-column load tables, and the Walk Test."
---

# ICM Architect & Workspace Validator

## Overview
This skill operationalizes **Jake Van Clief's Interpretable Context Methodology (ICM / MWP, arXiv:2603.16021)** across Hermes Agent OS. It ensures the workspace functions as an interpretable filesystem state machine.

## Invariant Rules
1. **Layer 0 (Global Rules)**: Compact root `AGENTS.md` (symlinked to `CLAUDE.md`).
2. **Layer 1 (Workspace Scope)**: `CONTEXT.md` with explicit Exclusion Tables.
3. **Layer 2 (Stage Gate Folders)**: Numbered directories (`01_spec/`, `02_impl/`, `03_verify/`) with `CONTEXT.md` <= 80 lines.
4. **Layer 3 (Factory / Immutables)**: Rules, schemas, and references in `rules/` and `_config/` <= 200 lines per file.
5. **Layer 4 (Product / Mutables)**: Output artifacts, code diffs, and verification receipts.

## Selective Section Routing Table Standard
Stage inputs must be specified using 4-column tables:
| Source | File / Location | Section / Scope | Why |
| :--- | :--- | :--- | :--- |

## Verification Command
```bash
python3 /var/home/imshubhamsocial/Projects/Workspace/Personal/hermes/scripts/hermes_icm_validator.py
```
