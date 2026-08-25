"""
Contract Tests for U28: GitHub Ingestion & Workplace Repo Maintenance
======================================================================
Tests stack detection, manifest discovery, test command inference,
AST symbol index integration, and onboarding summary generation.
"""

from __future__ import annotations

import sys
import tempfile
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import pytest

from hermes_core.repo_onboard import (
    RepoOnboarder,
    ProjectStackInfo,
    create_repo_onboarder,
)


class TestRepoOnboarder:
    """Test suite for U28 capabilities."""

    def test_python_project_stack_detection(self):
        with tempfile.TemporaryDirectory() as td:
            repo_path = Path(td)
            (repo_path / "pyproject.toml").write_text("[project]\nname = 'demo'")
            (repo_path / "main.py").write_text("def run():\n    return 42\n")
            (repo_path / "test_main.py").write_text("def test_run(): pass\n")

            onboarder = create_repo_onboarder(workspace_root=repo_path)
            info = onboarder.onboard(repo_path, index_symbols=True)

            assert info.primary_language == "Python"
            assert "pyproject.toml" in info.manifests
            assert info.test_command == "pytest"
            assert "main.py" in info.entrypoints
            assert info.symbol_count >= 2
            assert info.files_indexed >= 2

    def test_rust_project_stack_detection(self):
        with tempfile.TemporaryDirectory() as td:
            repo_path = Path(td)
            (repo_path / "Cargo.toml").write_text("[package]\nname = 'rust_demo'")
            src_dir = repo_path / "src"
            src_dir.mkdir()
            (src_dir / "main.rs").write_text("fn main() {}")

            onboarder = create_repo_onboarder(workspace_root=repo_path)
            info = onboarder.detect_stack(repo_path)

            assert info.primary_language == "Rust"
            assert "Cargo.toml" in info.manifests
            assert info.test_command == "cargo test"
            assert "src/main.rs" in info.entrypoints

    def test_onboarding_summary_generation(self):
        info = ProjectStackInfo(
            primary_language="Python",
            languages=["Python", "HTML/Web"],
            manifests=["pyproject.toml"],
            test_framework="pytest",
            test_command="pytest",
            symbol_count=120,
            files_indexed=8,
            entrypoints=["main.py"],
        )
        onboarder = create_repo_onboarder()
        summary = onboarder.generate_onboarding_summary(info)

        assert "# Repository Onboarding Report" in summary
        assert "Python" in summary
        assert "pyproject.toml" in summary
        assert "120 symbols" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
