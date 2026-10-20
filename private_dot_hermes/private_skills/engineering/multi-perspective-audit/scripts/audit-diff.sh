#!/usr/bin/env bash
# Audit uncommitted diffs against 4 axes
set -euo pipefail

echo "==> 1. Karpathy U12 3x Diff Limit & Diff Line Count:"
git diff --stat

echo "==> 2. Hardcoded Path Invariant Check (Law 9):"
git diff | grep -n "/var/home/imshubhamsocial" && { echo "FAILED: Hardcoded host path found!" >&2; exit 1; } || echo "PASSED: Zero host paths."

echo "==> 3. Linter Pass:"
ruff check . || true
