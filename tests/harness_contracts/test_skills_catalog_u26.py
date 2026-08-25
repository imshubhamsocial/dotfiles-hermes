"""
Contract Tests for U26: Upstream Plugin Standard & Awesome-Skills Catalog
==========================================================================
Tests the SkillsCatalogManager, standard plugin.yaml packaging, Two-Tier JIT
skill absorption, and token-bounded prompt injection.
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

from hermes_core.skills_catalog import (
    SkillsCatalogManager,
    SkillCatalogItem,
    create_skills_catalog_manager,
)


class TestSkillsCatalogManager:
    """Test suite for U26 capabilities."""

    def test_local_skill_installation_and_discovery(self):
        with tempfile.TemporaryDirectory() as td:
            plugins_dir = Path(td)
            manager = create_skills_catalog_manager(plugins_dir=plugins_dir)

            installed_path = manager.install_local_skill(
                name="webgl_shader_expert",
                skill_md_content="# WebGL Shader Expert\nGuides shader synthesis.",
                description="Expert GLSL shader compiler and uniforms manager",
                version="1.2.0",
                tags=["graphics", "webgl"],
            )

            assert installed_path.exists()
            assert (installed_path / "plugin.yaml").exists()
            assert (installed_path / "SKILL.md").exists()

            plugins = manager.list_installed_plugins()
            assert len(plugins) == 1
            assert plugins[0].name == "webgl_shader_expert"
            assert plugins[0].version == "1.2.0"

    def test_two_tier_jit_activation(self):
        with tempfile.TemporaryDirectory() as td:
            plugins_dir = Path(td)
            manager = create_skills_catalog_manager(plugins_dir=plugins_dir)

            manager.install_local_skill(
                name="ctf_exploit_runner",
                skill_md_content="# CTF Binary Exploit Guide\nPayload buffer overflow checks.",
                description="Disassembles ELF binaries and checks mitigations",
                version="2.0.0",
                tags=["security", "pwn"],
            )

            # Tier-1 prompt check (compact summary <= 150 tokens)
            tier1_block = manager.get_tier1_prompt_injection(max_tokens=150)
            assert "ctf_exploit_runner" in tier1_block
            assert len(tier1_block.splitlines()) == 1

            # Tier-2 JIT activation check (full body loaded on demand)
            activated = manager.activate_jit_skill("ctf_exploit_runner")
            assert activated is not None
            assert "Payload buffer overflow checks" in activated["skill_content"]
            assert activated["manifest"].name == "ctf_exploit_runner"

    def test_delete_skill(self):
        with tempfile.TemporaryDirectory() as td:
            plugins_dir = Path(td)
            manager = create_skills_catalog_manager(plugins_dir=plugins_dir)

            manager.install_local_skill(
                name="temporary_tool",
                skill_md_content="# Temp",
                description="Temporary skill",
            )
            assert len(manager.list_installed_plugins()) == 1

            deleted = manager.delete_skill("temporary_tool")
            assert deleted is True
            assert len(manager.list_installed_plugins()) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
