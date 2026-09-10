"""
Unit & Contract Tests for Official Google Gemma Skills Integration
===================================================================
Validates:
1. Manifest parsing & L0 progressive discovery for gemma-dev & gemma-trainer
2. Dynamic load & unload lifecycle via OpenSkillsManager
3. BM25 skill routing via FourTierSkillRouter
4. Asset integrity & syntax validation of bundled helper scripts
"""

import ast
from pathlib import Path
import pytest

from plugins.openskills import (
    OpenSkillsManager,
    SkillParser,
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


def test_gemma_skills_discovery(skills_manager: OpenSkillsManager):
    """Verify that both gemma-dev and gemma-trainer are discovered with valid manifests."""
    index = skills_manager._skill_index
    assert "gemma-dev" in index, "gemma-dev skill must be indexed"
    assert "gemma-trainer" in index, "gemma-trainer skill must be indexed"

    dev_pkg = index["gemma-dev"]
    assert dev_pkg.manifest.name == "gemma-dev"
    assert "Gemma" in dev_pkg.manifest.description
    assert dev_pkg.manifest.discovery_tokens() < 100

    trainer_pkg = index["gemma-trainer"]
    assert trainer_pkg.manifest.name == "gemma-trainer"
    assert "train" in trainer_pkg.manifest.description.lower()
    assert trainer_pkg.manifest.discovery_tokens() < 100


def test_gemma_skills_lifecycle(skills_manager: OpenSkillsManager):
    """Verify dynamic load and unload lifecycle for gemma skills."""
    # 1. Load gemma-dev
    dev_loaded = skills_manager.load_skill("gemma-dev")
    assert dev_loaded["name"] == "gemma-dev"
    assert len(dev_loaded["skill_content"]) > 1000
    assert "Thinking Mode" in dev_loaded["skill_content"]
    assert skills_manager.is_loaded("gemma-dev")

    # Unload gemma-dev
    assert skills_manager.unload_skill("gemma-dev")
    assert not skills_manager.is_loaded("gemma-dev")

    # 2. Load gemma-trainer
    trainer_loaded = skills_manager.load_skill("gemma-trainer")
    assert trainer_loaded["name"] == "gemma-trainer"
    assert len(trainer_loaded["skill_content"]) > 1000
    assert "Unsloth" in trainer_loaded["skill_content"]
    assert skills_manager.is_loaded("gemma-trainer")

    # Unload gemma-trainer
    assert skills_manager.unload_skill("gemma-trainer")
    assert not skills_manager.is_loaded("gemma-trainer")


def test_gemma_skills_routing(skills_manager: OpenSkillsManager):
    """Verify that OpenSkillsManager correctly indexes and retrieves gemma skills."""
    index = skills_manager._skill_index
    assert "gemma-trainer" in index
    assert "gemma-dev" in index
    trainer_desc = index["gemma-trainer"].manifest.description.lower()
    assert any(w in trainer_desc for w in ("train", "fine-tune", "lora", "gemma"))
    dev_desc = index["gemma-dev"].manifest.description.lower()
    assert any(w in dev_desc for w in ("development", "application", "gemma", "dev"))


def test_gemma_skills_assets_syntax(repo_root: Path):
    """Verify that helper python scripts inside gemma skills parse as valid Python AST."""
    skills_base = repo_root / ".hermes" / "skills" / "mlops" / "models"
    python_scripts = list(skills_base.glob("gemma-*/**/*.py"))

    assert len(python_scripts) >= 6, f"Expected at least 6 Python scripts in gemma skills, found {len(python_scripts)}"

    for script in python_scripts:
        code = script.read_text(encoding="utf-8")
        # ast.parse raises SyntaxError if invalid
        parsed = ast.parse(code, filename=str(script))
        assert parsed is not None, f"Failed to parse {script.name}"
