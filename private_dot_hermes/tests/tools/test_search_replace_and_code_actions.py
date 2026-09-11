"""
Contract Tests: SearchReplaceEngine & CodeActionExecutor (Phase 3)
=================================================================
Validates:
  1. Aider-style search-and-replace with unique matching and unified diff.
  2. Ambiguous and not-found search block rejections.
  3. SyntaxError prevention on Python file mutations.
  4. smolagents Code-as-Action AST preflight validation.
  5. Sandboxed code action execution with stdout/stderr capture.
  6. Execution timeout guard against runaway loops.
"""

from pathlib import Path
import pytest

from plugins.mcp_tools import SearchReplaceEngine, CodeActionExecutor


class TestSearchReplaceEngine:
    def test_search_replace_unique_success(self, tmp_path: Path):
        test_file = tmp_path / "app.py"
        test_file.write_text(
            "def calculate(x, y):\n"
            "    return x + y\n"
        )
        res = SearchReplaceEngine.search_replace(
            file_path=test_file,
            search_block="    return x + y",
            replace_block="    # multiply instead\n    return x * y",
        )
        assert res["success"] is True
        assert res["replaced_count"] == 1
        assert "-    return x + y" in res["diff"]
        assert "+    return x * y" in res["diff"]

        content = test_file.read_text()
        assert "return x * y" in content
        assert "return x + y" not in content

    def test_search_replace_not_found(self, tmp_path: Path):
        test_file = tmp_path / "app.py"
        test_file.write_text("def run():\n    pass\n")
        res = SearchReplaceEngine.search_replace(
            file_path=test_file,
            search_block="def missing():",
            replace_block="def found():",
        )
        assert res["success"] is False
        assert "not found" in res["error"].lower()

    def test_search_replace_ambiguous_rejected(self, tmp_path: Path):
        test_file = tmp_path / "app.py"
        test_file.write_text(
            "x = 10\n"
            "x = 10\n"
        )
        res = SearchReplaceEngine.search_replace(
            file_path=test_file,
            search_block="x = 10",
            replace_block="x = 20",
            allow_multiple=False,
        )
        assert res["success"] is False
        assert "ambiguous match" in res["error"].lower()

    def test_search_replace_syntax_error_rejected(self, tmp_path: Path):
        test_file = tmp_path / "script.py"
        test_file.write_text("def run():\n    return True\n")
        res = SearchReplaceEngine.search_replace(
            file_path=test_file,
            search_block="    return True",
            replace_block="    return (broken syntax def",
            validate_syntax=True,
        )
        assert res["success"] is False
        assert "syntaxerror" in res["error"].lower()
        # Original content must remain intact
        assert "return True" in test_file.read_text()


class TestCodeActionExecutor:
    def test_ast_preflight_valid(self):
        valid, err = CodeActionExecutor.validate_ast("def foo():\n    return 42\n")
        assert valid is True
        assert err is None

    def test_ast_preflight_invalid(self):
        valid, err = CodeActionExecutor.validate_ast("def foo():\n    return (\n")
        assert valid is False
        assert "syntaxerror" in err.lower()

    def test_execution_success(self, tmp_path: Path):
        code = "print('Hello from CodeAction')\nprint(40 + 2)"
        res = CodeActionExecutor.execute(code, workspace_dir=tmp_path)
        assert res["success"] is True
        assert res["exit_code"] == 0
        assert "Hello from CodeAction" in res["output"]
        assert "42" in res["output"]

    def test_execution_timeout_guard(self, tmp_path: Path):
        infinite_code = "import time\nwhile True:\n    time.sleep(0.1)\n"
        res = CodeActionExecutor.execute(infinite_code, timeout_seconds=1, workspace_dir=tmp_path)
        assert res["success"] is False
        assert res["exit_code"] == 124
        assert "timed out" in res["output"].lower()
