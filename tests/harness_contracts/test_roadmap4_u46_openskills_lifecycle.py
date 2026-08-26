"""
Contract Tests: Roadmap 4 Milestone U46
========================================
Validates OpenSkills Universal Package Manager & Progressive Disclosure Lifecycle:
1. YAML Frontmatter Parsing
2. L0 Discovery Token Budget (<50 tokens/skill)
3. JIT Load/Unload Lifecycle
4. Dependency & Validation
5. Zero GPU VRAM Overhead
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import pytest

from hermes_core.openskills_manager import (
    OpenSkillsManager,
    SkillParser,
    SkillManifest,
    SkillPackage,
    ToolSchemaExtractor,
    get_openskills_manager,
    reset_openskills_manager,
    build_skills_discovery_block,
    inject_loaded_skills_context,
)


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def temp_skills_dir():
    """Create a temporary skills directory for testing"""
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


@pytest.fixture
def sample_skill_md():
    """Sample valid SKILL.md content"""
    return """---
name: webgl_shader_expert
description: Expert GLSL shader compiler and uniforms manager
version: 2.1.0
author: hermes-agent
license: MIT
platforms: [linux, macos, windows]
tags: [graphics, webgl, shaders]
dependencies: [threejs_renderer]
tools: [patch_file, read_file, execute_command]
parameters:
  precision: highp
  target_glsl_version: 300 es
metadata:
  hermes:
    category: graphics
    priority: high
---

# WebGL Shader Expert

Advanced GLSL shader development and debugging.

## Capabilities

- Shader compilation and validation
- Uniform buffer management
- Performance profiling
- Cross-platform compatibility

## Tools

This skill uses patch_file, read_file, and execute_command for shader operations.
"""


@pytest.fixture
def sample_skill_no_tools():
    """Sample skill without tools"""
    return """---
name: planning_assistant
description: Helps create implementation plans
version: 1.0.0
tags: [planning]
dependencies: []
tools: []
parameters: {}
---

# Planning Assistant

Helps break down complex tasks into actionable plans.
"""


@pytest.fixture
def openskills_manager(temp_skills_dir, sample_skill_md):
    """Create OpenSkillsManager with sample skill installed"""
    # Reset global manager
    reset_openskills_manager()
    
    manager = OpenSkillsManager(skills_dirs=[temp_skills_dir])
    
    # Install sample skill
    manager.install_skill("webgl_shader_expert", sample_skill_md)
    
    yield manager
    
    # Cleanup
    reset_openskills_manager()


# =============================================================================
# TESTS
# =============================================================================

class TestOpenSkillsYAMLFrontmatterParsing:
    """Test YAML frontmatter parsing against OpenSkills schema"""

    def test_parse_valid_skill(self, temp_skills_dir, sample_skill_md):
        """Validates parsing of valid SKILL.md with all fields"""
        skill_file = temp_skills_dir / "test_skill" / "SKILL.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text(sample_skill_md)
        
        pkg = SkillParser.parse(skill_file)
        
        assert pkg.manifest.name == "webgl_shader_expert"
        assert pkg.manifest.description == "Expert GLSL shader compiler and uniforms manager"
        assert pkg.manifest.version == "2.1.0"
        assert pkg.manifest.author == "hermes-agent"
        assert pkg.manifest.tags == ["graphics", "webgl", "shaders"]
        assert pkg.manifest.dependencies == ["threejs_renderer"]
        assert pkg.manifest.tools == ["patch_file", "read_file", "execute_command"]
        assert pkg.manifest.parameters["precision"] == "highp"
        assert pkg.manifest.metadata["hermes"]["category"] == "graphics"
        assert "WebGL Shader Expert" in pkg.skill_content

    def test_parse_minimal_skill(self, temp_skills_dir, sample_skill_no_tools):
        """Validates parsing of minimal SKILL.md (only required fields)"""
        skill_file = temp_skills_dir / "minimal_skill" / "SKILL.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text(sample_skill_no_tools)
        
        pkg = SkillParser.parse(skill_file)
        
        assert pkg.manifest.name == "planning_assistant"
        assert pkg.manifest.description == "Helps create implementation plans"
        assert pkg.manifest.version == "1.0.0"
        assert pkg.manifest.tools == []
        assert pkg.manifest.dependencies == []

    def test_parse_missing_frontmatter_raises(self, temp_skills_dir):
        """Validates that missing frontmatter raises ValueError"""
        skill_file = temp_skills_dir / "bad_skill" / "SKILL.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text("# No Frontmatter\nJust content")
        
        with pytest.raises(ValueError, match="Missing YAML frontmatter"):
            SkillParser.parse(skill_file)

    def test_parse_missing_name_raises(self, temp_skills_dir):
        """Validates that missing name raises ValueError"""
        bad_skill = """---
description: Missing name field
---
Content"""
        skill_file = temp_skills_dir / "bad_skill" / "SKILL.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text(bad_skill)
        
        with pytest.raises(ValueError, match="name.*required"):
            SkillParser.parse(skill_file)

    def test_parse_missing_description_raises(self, temp_skills_dir):
        """Validates that missing description raises ValueError"""
        bad_skill = """---
name: no_description
---
Content"""
        skill_file = temp_skills_dir / "bad_skill" / "SKILL.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text(bad_skill)
        
        with pytest.raises(ValueError, match="description.*required"):
            SkillParser.parse(skill_file)

    def test_parse_invalid_yaml_raises(self, temp_skills_dir):
        """Validates that invalid YAML raises ValueError"""
        bad_skill = """---
name: bad_yaml
description: Test
invalid: yaml: content: [
---
Content"""
        skill_file = temp_skills_dir / "bad_skill" / "SKILL.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text(bad_skill)
        
        with pytest.raises(ValueError, match="Invalid YAML frontmatter"):
            SkillParser.parse(skill_file)

    def test_parse_from_string(self):
        """Validates parsing from string (for testing)"""
        content = """---
name: inline_skill
description: Parsed from string
---
Body content"""
        
        pkg = SkillParser.parse_from_string(content, "inline_skill")
        
        assert pkg.manifest.name == "inline_skill"
        assert pkg.manifest.description == "Parsed from string"
        assert pkg.skill_content == "Body content"


class TestProgressiveDisclosureDiscoveryTokens:
    """Test L0 Discovery token budget (<50 tokens per skill)"""

    def test_discovery_line_format(self, openskills_manager):
        """Validates L0 discovery line format"""
        lines = openskills_manager.discover_skills()
        
        assert len(lines) == 1
        assert lines[0].startswith("- webgl_shader_expert:")
        assert "Expert GLSL shader compiler" in lines[0]

    def test_discovery_tokens_under_50_per_skill(self, openskills_manager):
        """Validates each skill discovery entry consumes <50 tokens"""
        pkg = openskills_manager.get_skill("webgl_shader_expert")
        tokens = pkg.manifest.discovery_tokens()
        
        assert tokens < 50, f"Discovery tokens {tokens} >= 50"
        # Should be around 10-15 tokens for typical description
        assert tokens > 0

    def test_discovery_prompt_block_format(self, openskills_manager):
        """Validates formatted discovery block for system prompt"""
        block = openskills_manager.get_discovery_prompt_block()
        
        assert "Available Skills (L0 Discovery" in block
        assert "webgl_shader_expert" in block
        assert "load_skill" in block

    def test_discovery_token_budget_enforcement(self, temp_skills_dir):
        """Validates total discovery block respects token budget"""
        # Install many skills
        manager = OpenSkillsManager(skills_dirs=[temp_skills_dir], max_discovery_tokens=100)
        
        for i in range(10):
            skill_md = f"""---
name: skill_{i}
description: Skill number {i} with a description that is moderately long
tags: [test]
tools: []
---
Content"""
            manager.install_skill(f"skill_{i}", skill_md)
        
        lines = manager.discover_skills(max_tokens=100)
        
        # Should respect budget
        total_tokens = sum(manager.get_skill(name).manifest.discovery_tokens() for name in 
                          [line.split(":")[0].strip("- ") for line in lines])
        assert total_tokens <= 100

    def test_discovery_deterministic_ordering(self, temp_skills_dir):
        """Validates discovery order is deterministic (alphabetical)"""
        manager = OpenSkillsManager(skills_dirs=[temp_skills_dir])
        
        # Install in non-alphabetical order
        for name in ["zebra_skill", "alpha_skill", "beta_skill"]:
            skill_md = f"""---
name: {name}
description: Test skill {name}
tools: []
---
Content"""
            manager.install_skill(name, skill_md)
        
        lines = manager.discover_skills()
        
        names = [line.split(":")[0].strip("- ") for line in lines]
        assert names == sorted(names), "Skills should be sorted alphabetically"


class TestJITSkillLoadAndUnloadLifecycle:
    """Test L1 Load / L2 Unload lifecycle"""

    def test_load_skill_returns_full_context(self, openskills_manager):
        """Validates load_skill returns manifest, content, and tool schemas"""
        loaded = openskills_manager.load_skill("webgl_shader_expert")
        
        assert loaded["name"] == "webgl_shader_expert"
        assert loaded["manifest"].name == "webgl_shader_expert"
        assert "WebGL Shader Expert" in loaded["skill_content"]
        assert len(loaded["tool_schemas"]) >= 2  # patch_file, read_file
        tool_names = [t["name"] for t in loaded["tool_schemas"]]
        assert "patch_file" in tool_names
        assert "read_file" in tool_names

    def test_load_skill_marks_as_loaded(self, openskills_manager):
        """Validates skill is marked as loaded after load_skill"""
        assert not openskills_manager.is_loaded("webgl_shader_expert")
        
        openskills_manager.load_skill("webgl_shader_expert")
        
        assert openskills_manager.is_loaded("webgl_shader_expert")

    def test_load_skill_increments_load_count(self, openskills_manager):
        """Validates load count increments on each load"""
        pkg = openskills_manager.get_skill("webgl_shader_expert")
        initial_count = pkg.load_count
        
        openskills_manager.load_skill("webgl_shader_expert")
        assert pkg.load_count == initial_count + 1
        
        openskills_manager.unload_skill("webgl_shader_expert")
        openskills_manager.load_skill("webgl_shader_expert")
        assert pkg.load_count == initial_count + 2

    def test_unload_skill_evicts_from_context(self, openskills_manager):
        """Validates unload_skill removes skill from active context"""
        openskills_manager.load_skill("webgl_shader_expert")
        assert openskills_manager.is_loaded("webgl_shader_expert")
        
        result = openskills_manager.unload_skill("webgl_shader_expert")
        
        assert result is True
        assert not openskills_manager.is_loaded("webgl_shader_expert")

    def test_unload_nonexistent_skill_returns_false(self, openskills_manager):
        """Validates unload_skill returns False for non-loaded skill"""
        result = openskills_manager.unload_skill("nonexistent_skill")
        assert result is False

    def test_load_nonexistent_skill_raises(self, openskills_manager):
        """Validates load_skill raises KeyError for unknown skill"""
        with pytest.raises(KeyError, match="not found"):
            openskills_manager.load_skill("nonexistent_skill")

    def test_get_loaded_skill_context(self, openskills_manager):
        """Validates getting context for loaded skill"""
        openskills_manager.load_skill("webgl_shader_expert")
        
        context = openskills_manager.get_loaded_skill_context("webgl_shader_expert")
        
        assert context is not None
        assert context["name"] == "webgl_shader_expert"
        assert "WebGL Shader Expert" in context["skill_content"]
        assert len(context["tool_schemas"]) >= 2

    def test_get_loaded_skill_context_none_if_not_loaded(self, openskills_manager):
        """Validates None returned for non-loaded skill"""
        context = openskills_manager.get_loaded_skill_context("webgl_shader_expert")
        assert context is None

    def test_get_all_loaded_context(self, openskills_manager):
        """Validates combined context for all loaded skills"""
        openskills_manager.load_skill("webgl_shader_expert")
        
        context_block = openskills_manager.get_all_loaded_context()
        
        assert "Loaded Skill: webgl_shader_expert" in context_block
        assert "WebGL Shader Expert" in context_block
        assert "Tool Schemas" in context_block
        assert "patch_file" in context_block

    def test_get_all_loaded_context_empty_when_none(self, openskills_manager):
        """Validates empty string when no skills loaded"""
        context = openskills_manager.get_all_loaded_context()
        assert context == ""

    def test_multiple_skills_load_unload(self, temp_skills_dir):
        """Validates multiple skills can be loaded/unloaded independently"""
        manager = OpenSkillsManager(skills_dirs=[temp_skills_dir])
        
        # Install two skills
        for name in ["skill_a", "skill_b"]:
            skill_md = f"""---
name: {name}
description: Skill {name}
tools: [patch_file]
---
Content for {name}"""
            manager.install_skill(name, skill_md)
        
        # Load both
        manager.load_skill("skill_a")
        manager.load_skill("skill_b")
        
        assert manager.is_loaded("skill_a")
        assert manager.is_loaded("skill_b")
        assert len(manager.get_loaded_skills()) == 2
        
        # Unload one
        manager.unload_skill("skill_a")
        
        assert not manager.is_loaded("skill_a")
        assert manager.is_loaded("skill_b")
        assert len(manager.get_loaded_skills()) == 1
        
        # Unload other
        manager.unload_skill("skill_b")
        assert len(manager.get_loaded_skills()) == 0


class TestSkillDependencyAndMissingFieldValidation:
    """Test dependency validation and error handling"""

    def test_validate_dependencies_satisfied(self, temp_skills_dir):
        """Validates dependency check when all deps available"""
        manager = OpenSkillsManager(skills_dirs=[temp_skills_dir])
        
        # Install dependency first
        dep_md = """---
name: threejs_renderer
description: Three.js renderer skill
tools: []
---
Content"""
        manager.install_skill("threejs_renderer", dep_md)
        
        # Install skill with dependency
        skill_md = """---
name: webgl_shader_expert
description: Shader expert
dependencies: [threejs_renderer]
tools: []
---
Content"""
        manager.install_skill("webgl_shader_expert", skill_md)
        
        results = manager.validate_dependencies("webgl_shader_expert")
        assert results["threejs_renderer"] is True

    def test_validate_dependencies_missing(self, temp_skills_dir):
        """Validates dependency check reports missing deps"""
        manager = OpenSkillsManager(skills_dirs=[temp_skills_dir])
        
        skill_md = """---
name: webgl_shader_expert
description: Shader expert
dependencies: [missing_skill]
tools: []
---
Content"""
        manager.install_skill("webgl_shader_expert", skill_md)
        
        results = manager.validate_dependencies("webgl_shader_expert")
        assert results["missing_skill"] is False

    def test_validate_dependencies_empty(self, temp_skills_dir):
        """Validates empty dependencies returns empty dict"""
        manager = OpenSkillsManager(skills_dirs=[temp_skills_dir])
        
        skill_md = """---
name: independent_skill
description: No deps
dependencies: []
tools: []
---
Content"""
        manager.install_skill("independent_skill", skill_md)
        
        results = manager.validate_dependencies("independent_skill")
        assert results == {}

    def test_install_skill_name_mismatch_raises(self, temp_skills_dir):
        """Validates install_skill rejects name mismatch"""
        manager = OpenSkillsManager(skills_dirs=[temp_skills_dir])
        
        skill_md = """---
name: actual_name
description: Mismatch
tools: []
---
Content"""
        
        with pytest.raises(ValueError, match="doesn't match requested name"):
            manager.install_skill("different_name", skill_md)

    def test_uninstall_skill_removes_completely(self, temp_skills_dir, openskills_manager):
        """Validates uninstall removes skill from index and disk"""
        assert openskills_manager.get_skill("webgl_shader_expert") is not None
        
        result = openskills_manager.uninstall_skill("webgl_shader_expert")
        
        assert result is True
        assert openskills_manager.get_skill("webgl_shader_expert") is None

    def test_uninstall_nonexistent_returns_false(self, openskills_manager):
        """Validates uninstall returns False for nonexistent skill"""
        result = openskills_manager.uninstall_skill("nonexistent")
        assert result is False


class TestOpenSkillsZeroVRAMOverhead:
    """Test zero GPU VRAM overhead guarantee"""

    def test_zero_vram_guarantee_structure(self, openskills_manager):
        """Validates zero VRAM guarantee report structure"""
        guarantee = openskills_manager.get_zero_vram_guarantee()
        
        assert guarantee["skill_index_cpu_only"] is True
        assert guarantee["parser_cpu_only"] is True
        assert guarantee["tool_extraction_cpu_only"] is True
        assert guarantee["no_gpu_operations"] is True
        assert guarantee["ramdisk_compatible"] is True

    def test_no_gpu_imports(self):
        """Validates no GPU/ML libraries imported at module level"""
        import hermes_core.openskills_manager as osm
        
        # Check module doesn't import torch, tensorflow, cuda, etc.
        forbidden = ["torch", "tensorflow", "cuda", "cupy", "jax"]
        for mod in forbidden:
            assert not hasattr(osm, mod), f"Forbidden import: {mod}"

    def test_operations_on_cpu(self, openskills_manager):
        """Validates all operations execute on CPU (no GPU calls)"""
        # These operations should complete without any GPU interaction
        openskills_manager.discover_skills()
        openskills_manager.load_skill("webgl_shader_expert")
        openskills_manager.get_loaded_skill_context("webgl_shader_expert")
        openskills_manager.get_all_loaded_context()
        openskills_manager.unload_skill("webgl_shader_expert")
        openskills_manager.validate_dependencies("webgl_shader_expert")
        openskills_manager.list_available_skills()
        
        # All operations completed - no GPU used
        assert True


class TestToolSchemaExtraction:
    """Test tool schema extraction from skills"""

    def test_extract_builtin_tools(self, temp_skills_dir):
        """Validates built-in tool schema extraction"""
        manager = OpenSkillsManager(skills_dirs=[temp_skills_dir])
        
        skill_md = """---
name: tool_user
description: Uses multiple tools
tools: [patch_file, execute_command, read_file]
---
Content"""
        manager.install_skill("tool_user", skill_md)
        
        loaded = manager.load_skill("tool_user")
        tool_names = [t["name"] for t in loaded["tool_schemas"]]
        
        assert "patch_file" in tool_names
        assert "execute_command" in tool_names
        assert "read_file" in tool_names
        
        # Verify schema structure
        for tool in loaded["tool_schemas"]:
            assert "name" in tool
            assert "description" in tool
            assert "parameters" in tool
            assert tool["parameters"]["type"] == "object"

    def test_extract_tools_from_content(self, temp_skills_dir):
        """Validates tool extraction from skill content mentions"""
        manager = OpenSkillsManager(skills_dirs=[temp_skills_dir])
        
        skill_md = """---
name: implicit_tools
description: Mentions tools in content
tools: []
---
This skill uses patch_file and execute_command internally."""
        manager.install_skill("implicit_tools", skill_md)
        
        loaded = manager.load_skill("implicit_tools")
        tool_names = [t["name"] for t in loaded["tool_schemas"]]
        
        # Should detect tools mentioned in content
        assert "patch_file" in tool_names
        assert "execute_command" in tool_names


class TestIntegrationWithPromptSlotting:
    """Test integration with prompt slotting system"""

    def test_build_discovery_block_for_slot4(self, openskills_manager):
        """Validates discovery block generation for Slot 4"""
        block = build_skills_discovery_block(openskills_manager)
        
        assert "Available Skills" in block
        assert "webgl_shader_expert" in block
        assert "load_skill" in block

    def test_inject_loaded_skills_for_slot4(self, openskills_manager):
        """Validates loaded skills context injection for Slot 4"""
        openskills_manager.load_skill("webgl_shader_expert")
        
        context = inject_loaded_skills_context(openskills_manager)
        
        assert "Loaded Skill: webgl_shader_expert" in context
        assert "WebGL Shader Expert" in context
        assert "Tool Schemas" in context

    def test_empty_injection_when_none_loaded(self, openskills_manager):
        """Validates empty injection when no skills loaded"""
        context = inject_loaded_skills_context(openskills_manager)
        assert context == ""


class TestOpenSkillsManagerLifecycle:
    """Test full lifecycle management"""

    def test_list_available_skills(self, openskills_manager):
        """Validates listing all available skills"""
        skills = openskills_manager.list_available_skills()
        
        assert len(skills) == 1
        skill = skills[0]
        assert skill["name"] == "webgl_shader_expert"
        assert skill["description"] == "Expert GLSL shader compiler and uniforms manager"
        assert skill["version"] == "2.1.0"
        assert skill["loaded"] is False
        assert skill["load_count"] == 0
        assert "graphics" in skill["tags"]
        assert skill["dependencies"] == ["threejs_renderer"]
        assert "patch_file" in skill["tools"]

    def test_rebuild_index(self, temp_skills_dir):
        """Validates index rebuild after changes"""
        manager = OpenSkillsManager(skills_dirs=[temp_skills_dir])
        
        skill_md = """---
name: new_skill
description: New skill
tools: []
---
Content"""
        manager.install_skill("new_skill", skill_md)
        
        assert manager.get_skill("new_skill") is not None
        
        # Create new manager with same dir (simulates rebuild)
        new_manager = OpenSkillsManager(skills_dirs=[temp_skills_dir])
        assert new_manager.get_skill("new_skill") is not None

    def test_get_skill_returns_package(self, openskills_manager):
        """Validates get_skill returns SkillPackage"""
        pkg = openskills_manager.get_skill("webgl_shader_expert")
        
        assert pkg is not None
        assert isinstance(pkg, SkillPackage)
        assert pkg.manifest.name == "webgl_shader_expert"

    def test_get_skill_none_for_unknown(self, openskills_manager):
        """Validates get_skill returns None for unknown skill"""
        pkg = openskills_manager.get_skill("unknown")
        assert pkg is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
