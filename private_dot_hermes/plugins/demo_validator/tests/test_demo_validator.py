"""
Contract Tests for demo_validator plugin
========================================
Verifies HTML and JavaScript validation using Biome and Tree-sitter AST.
"""

import tempfile
from pathlib import Path
import pytest

from plugins.demo_validator import validate_html, validate_js, validate_artifact


def test_valid_html_validation():
    code = '<!DOCTYPE html><html lang="en"><head><title>Test</title></head><body><h1>Hello</h1></body></html>'
    passed, msg, checks = validate_html(code)
    assert passed is True
    assert "passed" in msg.lower()


def test_invalid_html_syntax_rejected():
    code = '<div><p>Unclosed paragraph'
    passed, msg, checks = validate_html(code)
    assert passed is False
    assert "error" in msg.lower() or "syntax" in msg.lower()


def test_valid_js_validation():
    code = 'function calculateSum(a, b) {\n    return a + b;\n}\n'
    passed, msg, checks = validate_js(code)
    assert passed is True
    assert "passed" in msg.lower()


def test_invalid_js_syntax_rejected():
    code = 'function invalid( { return 1; }'
    passed, msg, checks = validate_js(code)
    assert passed is False
    assert "error" in msg.lower() or "syntax" in msg.lower()


def test_validate_artifact_file():
    with tempfile.NamedTemporaryFile(suffix=".html", mode="w", delete=False, encoding="utf-8") as f:
        f.write('<!DOCTYPE html><html lang="en"><head><title>App</title></head><body><div>Content</div></body></html>')
        path = f.name

    try:
        res = validate_artifact(path)
        assert res["passed"] is True
        assert res["verdict"] == "APPROVED"
    finally:
        Path(path).unlink()
