"""
Contract Tests: Litho C4 Architecture Documentation & AST Symbol Graph
======================================================================
Validates:
  1. CodebaseSymbolIndex scans Python files and builds class/function graph.
  2. C4ArchitectureGenerator creates Markdown spec with Mermaid C4 diagrams.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
import pytest

from plugins.symbol_index import CodebaseSymbolIndex, C4ArchitectureGenerator


def test_codebase_symbol_index_scan(tmp_path):
    f1 = tmp_path / "mod_a.py"
    f1.write_text("class Alpha:\n    def run(self):\n        pass\n\ndef helper():\n    pass\n", encoding="utf-8")

    f2 = tmp_path / "mod_b.py"
    f2.write_text("import mod_a\n\nclass Beta(mod_a.Alpha):\n    pass\n", encoding="utf-8")

    index = CodebaseSymbolIndex(root_dir=tmp_path)
    stats = index.scan()
    assert stats["total_files"] == 2
    assert stats["total_classes"] == 2
    assert stats["total_functions"] == 2
    assert len(index.symbols) == 2


def test_c4_architecture_generator(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "service.py").write_text("class CoreService:\n    def start(self):\n        pass\n", encoding="utf-8")

    index = CodebaseSymbolIndex(root_dir=tmp_path)
    doc_out = tmp_path / "docs" / "c4.md"

    res = C4ArchitectureGenerator.generate(index, output_file=doc_out)
    assert res["status"] == "GENERATED_SUCCESSFULLY"
    assert doc_out.exists()

    content = doc_out.read_text(encoding="utf-8")
    assert "System Context Diagram" in content
    assert "Container Diagram" in content
    assert "graph TD" in content
    assert "CoreService" in content
