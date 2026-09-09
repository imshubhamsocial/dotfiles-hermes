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

from hermes_core.openskills_manager import (
    OpenSkillsManager,
    get_openskills_manager,
    reset_openskills_manager,
)
from hermes_core.second_brain import SecondBrain
from hermes_core.skill_router import FourTierSkillRouter


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


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


def test_graphify_skill_routing(repo_root: Path):
    """Verify FourTierSkillRouter correctly routes codebase architecture queries to graphify."""
    router = FourTierSkillRouter(repo_root=repo_root)
    hits = router.index.search("codebase architecture knowledge graph AST file relationships")
    assert any(stub.name == "graphify" for stub, _ in hits), (
        "graphify skill should be retrieved for codebase architecture queries"
    )


def test_graphify_runtime_isolation():
    """Verify Law #8: graphifyy library must NOT be installed in the core python environment."""
    with pytest.raises(ModuleNotFoundError):
        import graphifyy  # type: ignore


def test_graphify_extraction_and_second_brain_bridge(repo_root: Path):
    """End-to-end contract test for headless AST extraction and SecondBrain bridge."""
    import sys
    scripts_dir = repo_root / ".hermes"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))

    from scripts.build_codebase_graph import (
        find_graphify_binary,
        extract_codebase_graph,
        export_wiki,
        bridge_wiki_to_second_brain,
    )

    try:
        bin_path = find_graphify_binary()
    except FileNotFoundError:
        pytest.skip("graphify executable not found in host environment")

    assert bin_path.exists() and os.access(bin_path, os.X_OK)

    with tempfile.TemporaryDirectory() as td:
        temp_dir = Path(td)
        code_dir = temp_dir / "src"
        code_dir.mkdir()

        # Create a small dummy module
        sample_file = code_dir / "sample_service.py"
        sample_file.write_text(
            "class SampleService:\n"
            "    def execute_task(self, query: str) -> bool:\n"
            "        return len(query) > 0\n"
            "\n"
            "def run_sample_worker():\n"
            "    service = SampleService()\n"
            "    return service.execute_task('test')\n",
            encoding="utf-8",
        )

        out_dir = temp_dir / "out"
        graph_json = extract_codebase_graph(code_dir, out_dir, graphify_bin=bin_path, code_only=True)
        assert graph_json.exists(), "graph.json must be generated"

        wiki_dir = export_wiki(graph_json, graphify_bin=bin_path)
        assert wiki_dir.exists(), "wiki directory must be generated"
        assert (wiki_dir / "index.md").exists(), "wiki/index.md must be generated"

        # Bridge into a temporary SecondBrain
        sb_dir = temp_dir / "second_brain"
        sb = SecondBrain(root_dir=sb_dir)
        saved_cards = bridge_wiki_to_second_brain(wiki_dir, second_brain=sb, tag_prefix="test-graph")
        assert len(saved_cards) > 0, "At least one community card must be saved to SecondBrain"

        # Query SecondBrain for the AST concept
        hits = sb.search("SampleService")
        assert len(hits) > 0, "SecondBrain should locate SampleService card"
        assert "SampleService" in hits[0].content
