---
name: karpathy-surgical-diff
description: Surgical edits under Karpathy U12 limit
---
# Karpathy Surgical Diff Playbook
1. Always mutate modules via jev_mutate_module with a unique target_pattern.
2. Changes must not exceed 15 lines or 3x the defective block size.
3. Pre-write AST validation and post-write ruff linter check execute automatically.
