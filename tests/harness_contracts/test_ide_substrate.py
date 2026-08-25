#!/usr/bin/env python3
"""
Phase-2 Contract Spike: IDE Knowledge Substrate (U20)
=====================================================
Versioned contract test for Phase 2 (roadmap §3.4-B).

  - U20 Type Signature Resolver: loads authoritative type definitions from
    types/ directory; resolves exact single-line signatures on demand;
    eliminates parametric memory hallucination for 4B SLMs.
  - U20 Symbol Index: lightweight SQLite-backed workspace symbol indexer;
    sub-2ms query latency on RAMDisk (/dev/shm).
  - U20 Scaffold Registry: pre-baked gold-standard project templates;
    @architect emits template reference, @coder patches surgically.

100% offline & deterministic.
Run: pytest tests/harness_contracts/test_ide_substrate.py -q
"""

from __future__ import annotations

import sqlite3
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from hermes_core.ide_substrate import (  # noqa: E402
    TypeSignatureResolver,
    SymbolIndex,
    ScaffoldRegistry,
    get_type_signature,
    get_scaffold,
    _load_type_file,
    _discover_type_files,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def types_root():
    """Point to the project's types/ directory."""
    return ROOT / "types"


@pytest.fixture()
def resolver(types_root):
    return TypeSignatureResolver(types_root=types_root)


@pytest.fixture()
def scaffold_root():
    return ROOT / "types" / "templates"


@pytest.fixture()
def scaffold(scaffold_root):
    return ScaffoldRegistry(templates_root=scaffold_root)


@pytest.fixture()
def symbol_index(tmp_path):
    db = tmp_path / "test_symbols.db"
    return SymbolIndex(db_path=db)


# ---------------------------------------------------------------------------
# U20 — Type Signature Resolver
# ---------------------------------------------------------------------------

class TestU20TypeResolver:
    def test_resolve_buffergeometry(self, resolver):
        sig = resolver.resolve("BufferGeometry")
        assert sig is not None
        assert "BufferGeometry" in sig

    def test_resolve_three_prefixed(self, resolver):
        sig = resolver.resolve("THREE.BufferGeometry")
        assert sig is not None
        assert "BufferGeometry" in sig

    def test_resolve_posix_epoll_event(self, resolver):
        sig = resolver.resolve("epoll_event")
        assert sig is not None
        assert "struct" in sig.lower() or "epoll" in sig.lower()

    def test_resolve_posix_prefixed(self, resolver):
        sig = resolver.resolve("POSIX.epoll_event")
        assert sig is not None

    def test_resolve_node_readFileSync(self, resolver):
        sig = resolver.resolve("readFileSync")
        assert sig is not None
        assert "path" in sig.lower() or "string" in sig.lower()

    def test_resolve_nonexistent_returns_none(self, resolver):
        assert resolver.resolve("NonExistentType12345") is None

    def test_list_categories(self, resolver):
        cats = resolver.list_categories()
        assert "posix" in cats
        assert "threejs" in cats
        assert "nodejs" in cats

    def test_list_symbols_in_category(self, resolver):
        syms = resolver.list_symbols("threejs")
        assert "BufferGeometry" in syms
        assert "Vector3" in syms

    def test_list_all_symbols(self, resolver):
        syms = resolver.list_symbols()
        assert len(syms) > 20  # at least 20 symbols across all categories

    def test_summary_tokens_under_budget(self, resolver):
        tokens = resolver.summary_tokens()
        assert tokens <= 30  # very compact summary

    def test_global_convenience_api(self):
        sig = get_type_signature("Vector3")
        assert sig is not None
        assert "Vector3" in sig

    def test_load_type_file_directly(self):
        path = ROOT / "types" / "threejs" / "threejs_types.types"
        syms = _load_type_file(path)
        assert "BufferGeometry" in syms
        assert "Vector3" in syms

    def test_discover_type_files(self, types_root):
        registry = _discover_type_files(types_root)
        assert "threejs" in registry
        assert "posix" in registry
        assert "nodejs" in registry
        assert "BufferGeometry" in registry["threejs"]


# ---------------------------------------------------------------------------
# U20 — Symbol Index (SQLite)
# ---------------------------------------------------------------------------

class TestU20SymbolIndex:
    def test_index_python_file(self, symbol_index):
        py_code = "def hello():\n    pass\n\nclass Foo:\n    def bar(self):\n        pass\n"
        count = symbol_index.index_file("test.py", py_code)
        assert count == 3  # hello, Foo, bar

    def test_index_javascript_file(self, symbol_index):
        js_code = "function greet() {}\nconst PI = 3.14;\nclass App {}\n"
        count = symbol_index.index_file("app.js", js_code)
        assert count == 3  # greet, PI, App

    def test_query_exact_match(self, symbol_index):
        symbol_index.index_file("mod.py", "def compute():\n    return 42\n")
        results = symbol_index.query("compute")
        assert len(results) >= 1
        assert results[0]["name"] == "compute"
        assert results[0]["kind"] == "function"
        assert results[0]["file"] == "mod.py"

    def test_query_substring_match(self, symbol_index):
        symbol_index.index_file("a.py", "def get_user_data():\n    pass\n")
        symbol_index.index_file("b.py", "def get_config():\n    pass\n")
        results = symbol_index.query("get_")
        assert len(results) >= 2

    def test_query_returns_line_number(self, symbol_index):
        symbol_index.index_file("x.py", "line1\nline2\ndef target():\n    pass\n")
        results = symbol_index.query("target")
        assert results[0]["line"] == 3

    def test_query_latency_under_2ms(self, symbol_index):
        for i in range(100):
            symbol_index.index_file(f"mod{i}.py", f"def func_{i}():\n    pass\n")
        t0 = time.perf_counter()
        symbol_index.query("func_50")
        elapsed_ms = (time.perf_counter() - t0) * 1000
        assert elapsed_ms < 2.0, f"Query took {elapsed_ms:.3f}ms, budget is 2ms"

    def test_index_nonexistent_file_returns_zero(self, symbol_index):
        assert symbol_index.index_file("nope.py") == 0

    def test_clear_removes_all_symbols(self, symbol_index):
        symbol_index.index_file("a.py", "def x(): pass\n")
        assert symbol_index.query("x")
        symbol_index.clear()
        assert symbol_index.query("x") == []

    def test_query_empty_index(self, symbol_index):
        assert symbol_index.query("anything") == []


# ---------------------------------------------------------------------------
# U20 — Scaffold Registry
# ---------------------------------------------------------------------------

class TestU20ScaffoldRegistry:
    def test_list_templates(self, scaffold):
        templates = scaffold.list_templates()
        names = [t["name"] for t in templates]
        assert "webgl_canvas_boilerplate.html" in names
        assert "posix_worker_pool.py" in names
        assert "playwright_tdd_spec.py" in names

    def test_get_template_content(self, scaffold):
        content = scaffold.get_template("webgl_canvas_boilerplate.html")
        assert content is not None
        assert "THREE.Scene" in content
        assert "requestAnimationFrame" in content

    def test_get_nonexistent_template(self, scaffold):
        assert scaffold.get_template("nonexistent.html") is None

    def test_get_summary_lightweight(self, scaffold):
        summary = scaffold.get_summary("webgl_canvas_boilerplate.html")
        assert summary is not None
        assert len(summary.splitlines()) <= 5

    def test_scaffold_tokens_under_budget(self, scaffold):
        tokens = scaffold.scaffold_tokens()
        assert tokens <= 30  # very compact listing

    def test_global_convenience_api(self):
        content = get_scaffold("webgl_canvas_boilerplate.html")
        assert content is not None
        assert "THREE" in content

    def test_template_metadata_includes_size(self, scaffold):
        templates = scaffold.list_templates()
        for t in templates:
            assert "size_bytes" in t
            assert t["size_bytes"] > 0


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
