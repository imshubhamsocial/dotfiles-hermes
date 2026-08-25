"""
U36 Contract Tests: Context Sieve & Multi-File PageRank Spine
==============================================================
Validates:
  1. build_repo_spine() produces architectural spine < 1,000 tokens
  2. slice_relevant_context() extracts targeted slices < 500 tokens
  3. compress_diff_context() minimizes diff token overhead
  4. SQLite WAL cache persists across invocations
  4. Integration with SymbolGraph (U22)
"""

import os
import tempfile
import pytest
from pathlib import Path

from hermes_core.context_sieve import ContextSieve, create_ramdisk_sieve
from hermes_core.token_engine import estimate_tokens


class TestContextSieveU36:
    """Contract tests for U36 Multi-File Context Sieve."""

    @pytest.fixture
    def temp_repo(self):
        """Create a temporary repo with multi-file structure for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            # Main entry point
            (root / "main.py").write_text("""
from utils import helper
from services import api_service

def main():
    data = helper.load_data()
    api_service.process(data)
    print("Done")

if __name__ == "__main__":
    main()
""")

            # Utility module
            (root / "utils.py").write_text("""
import json
from typing import List, Dict

def load_data() -> List[Dict]:
    return [{"id": 1, "name": "test"}]

def parse_json(text: str) -> Dict:
    return json.loads(text)

class DataProcessor:
    def __init__(self):
        self.buffer = []

    def add(self, item):
        self.buffer.append(item)

    def flush(self):
        result = self.buffer
        self.buffer = []
        return result
""")

            # Services module
            (root / "services").mkdir()
            (root / "services" / "api_service.py").write_text("""
from utils import parse_json

class APIService:
    def __init__(self, endpoint: str):
        self.endpoint = endpoint

    def process(self, data):
        for item in data:
            self._send(item)

    def _send(self, item):
        print(f"Sending {item} to {self.endpoint}")

    def health_check(self) -> bool:
        return True
""")

            # Config module
            (root / "config.py").write_text("""
CONFIG = {
    "api_endpoint": "http://localhost:8080",
    "timeout": 30,
    "retries": 3,
}

def get_config(key: str):
    return CONFIG.get(key)
""")

            # Tests
            (root / "tests").mkdir()
            (root / "tests" / "test_utils.py").write_text("""
import pytest
from utils import load_data, parse_json, DataProcessor

def test_load_data():
    data = load_data()
    assert len(data) == 1
    assert data[0]["id"] == 1

def test_parse_json():
    result = parse_json('{"a": 1}')
    assert result == {"a": 1}

def test_data_processor():
    dp = DataProcessor()
    dp.add("x")
    dp.add("y")
    assert dp.flush() == ["x", "y"]
""")

            yield str(root)

    @pytest.fixture
    def sieve(self):
        """Fresh ContextSieve instance with RAMDisk cache."""
        return create_ramdisk_sieve()

    def test_build_repo_spine_token_budget(self, temp_repo, sieve):
        """Spine must be under 1,000 tokens."""
        spine = sieve.build_repo_spine(temp_repo, max_tokens=1000)
        token_count = estimate_tokens(spine)
        assert token_count < 1000, f"Spine {token_count} tokens exceeds 1000 budget"
        assert "REPO SPINE" in spine
        assert "main.py" in spine or "utils.py" in spine or "services" in spine

    def test_build_repo_spine_structure(self, temp_repo, sieve):
        """Spine contains architectural elements: classes, functions, entrypoints."""
        spine = sieve.build_repo_spine(temp_repo)
        # Should identify key symbols
        assert any(k in spine for k in ["class:", "function:", "kind:"])
        # Should show PageRank scores
        assert "PR=" in spine

    def test_slice_relevant_context_token_budget(self, temp_repo, sieve):
        """Targeted slice must be under 500 tokens."""
        slice_text = sieve.slice_relevant_context(temp_repo, ["APIService", "process"], max_tokens=500)
        token_count = estimate_tokens(slice_text)
        assert token_count < 500, f"Slice {token_count} tokens exceeds 500 budget"
        assert "SLICE" in slice_text
        assert "APIService" in slice_text or "process" in slice_text

    def test_slice_includes_callers_callees(self, temp_repo, sieve):
        """Slice includes immediate caller/callee signatures."""
        slice_text = sieve.slice_relevant_context(temp_repo, ["DataProcessor"])
        # Should include DataProcessor and its methods
        assert "DataProcessor" in slice_text
        assert any(m in slice_text for m in ["add", "flush", "__init__"])

    def test_compress_diff_context(self, temp_repo, sieve):
        """Diff compression produces minimal unified diff."""
        target = Path(temp_repo) / "config.py"
        original = target.read_text()
        
        # Create a patch
        patch = original.replace('"timeout": 30', '"timeout": 60')
        
        diff = sieve.compress_diff_context(str(target), patch)
        assert "DIFF" in diff
        assert "- " in diff or "+ " in diff
        assert "timeout" in diff

    def test_diff_cache_persistence(self, temp_repo, sieve):
        """Diff cache persists across invocations."""
        target = Path(temp_repo) / "config.py"
        original = target.read_text()
        patch = original.replace('"retries": 3', '"retries": 5')
        
        # First call - populate cache
        diff1 = sieve.compress_diff_context(str(target), patch)
        
        # Second call - should hit cache (same patch_hash)
        diff2 = sieve.compress_diff_context(str(target), patch)
        
        assert diff1 == diff2

    def test_spine_cache_persistence(self, temp_repo, sieve):
        """Spine cache persists across invocations."""
        spine1 = sieve.build_repo_spine(temp_repo)
        
        # Create new sieve instance (simulates new process)
        sieve2 = create_ramdisk_sieve()
        spine2 = sieve2.build_repo_spine(temp_repo)
        
        assert spine1 == spine2

    def test_slice_cache_persistence(self, temp_repo, sieve):
        """Slice cache persists across invocations."""
        slice1 = sieve.slice_relevant_context(temp_repo, ["APIService"])
        
        sieve2 = create_ramdisk_sieve()
        slice2 = sieve2.slice_relevant_context(temp_repo, ["APIService"])
        
        assert slice1 == slice2

    def test_integration_with_symbol_graph(self, temp_repo, sieve):
        """ContextSieve can work alongside SymbolGraph for spine computation."""
        from hermes_core.symbol_graph import SymbolGraph, create_ramdisk_graph
        
        graph = create_ramdisk_graph()
        
        # Index the repo
        for ext in [".py"]:
            for f in Path(temp_repo).rglob(f"*{ext}"):
                if f.is_file():
                    content = f.read_text()
                    graph.index_source(str(f), content)
        
        # Build spine using sieve (which can use graph if passed)
        spine = sieve.build_repo_spine(temp_repo)
        assert len(spine) > 0
        assert "REPO SPINE" in spine

    def test_empty_repo_handling(self, sieve):
        """Handles empty or non-Python repo gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a non-Python file
            Path(tmpdir, "README.md").write_text("# Test")
            spine = sieve.build_repo_spine(tmpdir)
            assert "No symbols found" in spine or "REPO SPINE" in spine

    def test_malformed_python_handling(self, sieve):
        """Handles syntax errors in source files gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "bad.py").write_text("def broken(:\n    pass")
            # Should not crash
            spine = sieve.build_repo_spine(tmpdir)
            assert isinstance(spine, str)

    def test_js_ts_files_included(self, temp_repo, sieve):
        """JS/TS files are included in spine extraction."""
        js_file = Path(temp_repo) / "app.js"
        js_file.write_text("""
class Component {
    constructor() {
        this.state = {};
    }
    render() {
        return this.state;
    }
}

function bootstrap() {
    const c = new Component();
    return c.render();
}
""")
        spine = sieve.build_repo_spine(temp_repo)
        assert "Component" in spine or "app.js" in spine


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
