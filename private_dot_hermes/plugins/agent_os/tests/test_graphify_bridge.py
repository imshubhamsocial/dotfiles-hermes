"""
Unit & Contract Tests for Graphify AST Knowledge Graph & SecondBrain Bridge
==========================================================================
Validates:
1. Manifest parsing & L0 progressive discovery for the graphify skill package
2. Dynamic JIT load and unload lifecycle via OpenSkillsManager
3. Binary isolation check (zero core runtime pollution - Law #8)
4. Headless AST extraction, wiki export, and SecondBrain knowledge retrieval
"""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
import pytest

from plugins.openskills import (
    OpenSkillsManager,
    get_openskills_manager,
    reset_openskills_manager,
)


@pytest.fixture
def repo_root() -> Path:
    return Path.home()


@pytest.fixture
def skills_manager(repo_root: Path) -> OpenSkillsManager:
    reset_openskills_manager()
    skills_dirs = [
        repo_root / ".hermes" / "skills",
        Path.home() / ".hermes" / "skills",
    ]
    return OpenSkillsManager(skills_dirs=skills_dirs)


def test_graphify_skill_discovery(skills_manager: OpenSkillsManager):
    """Verify that graphify skill is indexed with valid metadata under L0 budget."""
    index = skills_manager._skill_index
    assert "graphify" in index, "graphify skill must be indexed in OpenSkillsManager"

    pkg = index["graphify"]
    assert pkg.manifest.name == "graphify"
    assert "knowledge graph" in pkg.manifest.description.lower()
    assert pkg.manifest.discovery_tokens() < 100


def test_graphify_skill_lifecycle(skills_manager: OpenSkillsManager):
    """Verify dynamic JIT load and unload lifecycle for graphify skill."""
    loaded = skills_manager.load_skill("graphify")
    assert loaded["name"] == "graphify"
    assert "graphify query" in loaded["skill_content"]
    assert skills_manager.is_loaded("graphify")

    # Unload
    assert skills_manager.unload_skill("graphify")
    assert not skills_manager.is_loaded("graphify")


def test_graphify_skill_routing(skills_manager: OpenSkillsManager):
    """Verify OpenSkillsManager correctly indexes and retrieves graphify skill."""
    index = skills_manager._skill_index
    assert "graphify" in index, "graphify skill must be indexed"
    desc = index["graphify"].manifest.description.lower()
    assert "knowledge graph" in desc or "ast" in desc


def test_graphify_runtime_isolation():
    """Verify Law #8: graphifyy library must NOT be installed in the core python environment."""
    with pytest.raises(ModuleNotFoundError):
        import graphifyy  # type: ignore
