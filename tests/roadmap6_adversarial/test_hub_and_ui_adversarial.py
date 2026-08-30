"""
Adversarial Hub Fleet & Generative UI Test Suite (Roadmap 6 - M4 & M5)
======================================================================
Tries to corrupt Hub JSON state, spawn rogue non-existent roles, verify offline
asset bundle byte integrity, and audit documentation search robustness.
"""

import json
import subprocess
import tempfile
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
BIN_DIR = ROOT / ".hermes/bin"
ASSETS_DIR = ROOT / ".hermes/assets/js"


class TestHubAndUIAdversarial:

    def test_hub_state_corruption_recovery(self):
        """Adversarial Goal: Write invalid JSON to hub state and verify CLI handles it cleanly without crashing."""
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            f.write("{ CORRUPTED JSON SYNTAX: [ }")
            corrupt_state = f.name

        try:
            # Point to corrupt state and run status
            import importlib.util
            spec = importlib.util.spec_from_file_location("hub_cli", str(BIN_DIR / "hub_cli.py"))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            # Override path
            mod.find_hub_state_path = lambda: Path(corrupt_state)
            state = mod.load_hub_state()
            assert "active_tasks" in state, "Failed to fall back to clean state on corruption"
        finally:
            Path(corrupt_state).unlink(missing_ok=True)

    def test_generative_ui_offline_assets_integrity(self):
        """Verifies that all 4 pre-cached offline UI bundles are present on disk and exceed 50 KB."""
        required_bundles = [
            ("chart.umd.min.js", 150_000),
            ("three.min.js", 400_000),
            ("d3.min.js", 200_000),
            ("katex.min.js", 150_000),
        ]
        for filename, min_bytes in required_bundles:
            bundle_path = ASSETS_DIR / filename
            assert bundle_path.exists(), f"Missing offline UI asset bundle: {bundle_path}"
            size = bundle_path.stat().st_size
            assert size >= min_bytes, f"Asset bundle {filename} is suspiciously small: {size} bytes (min: {min_bytes})"

    def test_doc_index_regex_fuzzing(self):
        """Adversarial Goal: Query the documentation indexer with special regex characters and fuzzy syntax."""
        fuzz_queries = [
            ".*+?^${}()|[]\\",
            "SELECT * FROM users WHERE '1'='1'",
            "<script>alert(1)</script>",
            "\\\\\\///&&&$$$@@@"
        ]
        for query in fuzz_queries:
            res = subprocess.run(
                ["python3.13", str(BIN_DIR / "index_docs.py"), "--query", query, "--json"],
                capture_output=True, text=True, timeout=5
            )
            assert res.returncode == 0, f"Indexer crashed on fuzz query '{query}': {res.stderr}"
