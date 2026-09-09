"""
Contract Tests: Multi-Bot Role Capability Isolation & Delegation
================================================================
Validates:
  1. Role capability masks enforcing separation of concerns:
     - @architect is read-only (no destructive file writes)
     - @tester runs tests and reviews (no direct code synthesis)
     - @coder performs surgical patches and edits
  2. AST validity verification on code candidates
"""

from __future__ import annotations

import ast
import pytest

ROLE_POLICIES: dict[str, set[str]] = {
    "architect": {"read_file", "search_files", "ast_search", "web_extract"},
    "tester": {"read_file", "execute_command", "run_test_suite"},
    "coder": {"read_file", "write_file", "patch_file", "execute_command"},
    "security": {"read_file", "audit_code", "ast_search"},
}


def test_capability_masks_trinity_isolation():
    """Verify @architect, @coder, and @tester tool isolation."""
    arch_tools = ROLE_POLICIES["architect"]
    assert "write_file" not in arch_tools
    assert "patch_file" not in arch_tools

    tester_tools = ROLE_POLICIES["tester"]
    assert "write_file" not in tester_tools
    assert "run_test_suite" in tester_tools

    coder_tools = ROLE_POLICIES["coder"]
    assert "write_file" in coder_tools
    assert "patch_file" in coder_tools


def test_ast_candidate_verification():
    """Verify AST parsing identifies valid vs broken Python code candidates."""
    valid_code = "def add(a: int, b: int) -> int:\n    return a + b\n"
    broken_code = "def add(a, b\n    return a + b\n"

    parsed_valid = ast.parse(valid_code)
    assert parsed_valid is not None

    with pytest.raises(SyntaxError):
        ast.parse(broken_code)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
