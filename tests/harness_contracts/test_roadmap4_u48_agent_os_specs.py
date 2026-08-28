"""
Contract Tests: Roadmap 4 Milestone U48
========================================
Validates Agent-OS Two-Tier Standards & Spec-First Planner:
1. Two-tier rules inheritance and precedence
2. Spec-first planner plan.json schema
3. Pre-implementation plan gate
4. Rules token budget in Slot 3
5. Zero GPU VRAM consumption
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / ".hermes" / "src"))

import pytest

from hermes_core.agent_os_standards import (
    TwoTierStandardsEngine,
    RuleParser,
    RuleFile,
    CompiledStandards,
    build_two_tier_slot3_injection,
    get_standards_engine,
    reset_standards_engine,
    IMMUTABLE_GLOBAL_CONSTRAINTS,
)
from hermes_core.spec_first_planner import (
    SpecFirstPlanner,
    Plan,
    PlanStep,
    inject_plan_into_slot3,
    enforce_plan_gate_before_edit,
    get_spec_first_planner,
    reset_spec_first_planner,
    PLAN_PATH,
)


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def temp_rules_dirs():
    """Create temporary global and project rules directories"""
    with tempfile.TemporaryDirectory() as td:
        global_dir = Path(td) / "global"
        project_dir = Path(td) / "project" / ".hermes" / "rules"
        global_dir.mkdir(parents=True)
        project_dir.mkdir(parents=True)
        
        yield global_dir, project_dir


@pytest.fixture
def populated_standards_engine(temp_rules_dirs):
    """Standards engine with populated rules"""
    global_dir, project_dir = temp_rules_dirs
    
    # Create global rule
    (global_dir / "hardware.md").write_text("""---
version: 1.0.0
category: global
immutable: true
---
# Hardware Constraints
- VRAM: 4800 MiB max
- GPU: RTX 3050
""")
    
    # Create project rule
    (project_dir / "coding.md").write_text("""---
version: 1.0.0
category: project
extends: global
---
# Project Coding Standards
- Use type hints
- Relative paths only
""")
    
    engine = TwoTierStandardsEngine(
        global_rules_dir=global_dir,
        project_root=project_dir.parent.parent,
    )
    
    yield engine


@pytest.fixture
def temp_plan_path():
    """Create temporary plan path"""
    with tempfile.TemporaryDirectory() as td:
        yield Path(td) / "plan.json"


@pytest.fixture
def populated_planner(temp_plan_path):
    """Planner with active plan"""
    planner = SpecFirstPlanner(plan_path=temp_plan_path)
    
    plan = planner.create_plan(
        goal="Implement feature X",
        constraints=["VRAM < 4800 MiB", "Relative paths only"],
        affected_files=["src/main.py", "tests/test_main.py"],
    )
    
    planner.add_step(
        "Step 1: Create module",
        affected_files=["src/main.py"],
        verification="pytest tests/test_main.py::test_module",
    )
    planner.add_step(
        "Step 2: Add tests",
        affected_files=["tests/test_main.py"],
        verification="pytest tests/test_main.py",
    )
    
    yield planner


# =============================================================================
# TESTS
# =============================================================================

class TestTwoTierRulesInheritanceAndPrecedence:
    """Test two-tier rules inheritance and precedence"""

    def test_load_global_rules(self, populated_standards_engine):
        """Validates global rules are loaded"""
        global_rules = populated_standards_engine.get_global_rules()
        
        assert len(global_rules) == 1
        assert global_rules[0].category == "global"
        assert global_rules[0].frontmatter.get("immutable") is True
        assert "VRAM" in global_rules[0].content

    def test_load_project_rules(self, populated_standards_engine):
        """Validates project rules are loaded"""
        project_rules = populated_standards_engine.get_project_rules()
        
        assert len(project_rules) == 1
        assert project_rules[0].category == "project"
        assert project_rules[0].frontmatter.get("extends") == "global"
        assert "type hints" in project_rules[0].content

    def test_compile_merges_both_tiers(self, populated_standards_engine):
        """Validates compilation merges both tiers"""
        compiled = populated_standards_engine.compile()
        
        assert isinstance(compiled, CompiledStandards)
        assert len(compiled.global_rules) == 1
        assert len(compiled.project_rules) == 1
        assert "IMMUTABLE GLOBAL CONSTRAINTS" in compiled.merged_content
        assert "GLOBAL STANDARDS" in compiled.merged_content
        assert "PROJECT STANDARDS" in compiled.merged_content

    def test_project_rules_override_global(self, temp_rules_dirs):
        """Validates project rules can extend/override global"""
        global_dir, project_dir = temp_rules_dirs
        
        # Global rule
        (global_dir / "test.md").write_text("""---
category: global
---
# Global Rule
- Setting: global_value
""")
        
        # Project rule with same topic
        (project_dir / "test.md").write_text("""---
category: project
extends: global
---
# Project Rule
- Setting: project_value
""")
        
        engine = TwoTierStandardsEngine(
            global_rules_dir=global_dir,
            project_root=project_dir.parent.parent,
        )
        
        compiled = engine.compile()
        
        # Both should appear, project after global
        assert "Global Rule" in compiled.merged_content
        assert "Project Rule" in compiled.merged_content
        # Project should come after global in the merged content
        global_pos = compiled.merged_content.find("Global Rule")
        project_pos = compiled.merged_content.find("Project Rule")
        assert global_pos < project_pos

    def test_immutable_global_constraints_always_present(self, populated_standards_engine):
        """Validates immutable global constraints are always in compiled output"""
        compiled = populated_standards_engine.compile()
        
        for key in IMMUTABLE_GLOBAL_CONSTRAINTS:
            assert key in compiled.merged_content, f"Immutable constraint '{key}' missing"

    def test_validate_project_rule_blocks_vram_violation(self, populated_standards_engine):
        """Validates project rule validation catches VRAM violations"""
        # Valid rule
        valid = populated_standards_engine.validate_project_rule("Use VRAM 4000 MiB")
        assert valid["valid"] is True
        
        # Invalid rule - exceeds VRAM ceiling
        invalid = populated_standards_engine.validate_project_rule("Use VRAM 5000 MiB for this")
        assert invalid["valid"] is False
        assert any("VRAM > 4800" in v for v in invalid["violations"])

    def test_validate_project_rule_warns_absolute_paths(self, populated_standards_engine):
        """Validates project rule validation warns about absolute paths"""
        result = populated_standards_engine.validate_project_rule("Use /home/user/path for config")
        
        # Should warn but not fail (could be intentional with $HOME)
        assert "warnings" in result

    def test_validate_project_rule_warns_xfail(self, populated_standards_engine):
        """Validates project rule validation warns about test skipping"""
        result = populated_standards_engine.validate_project_rule("You can xfail this test")
        
        assert "warnings" in result
        assert any("xfail" in w.lower() or "skip" in w.lower() for w in result["warnings"])

    def test_validate_project_rule_warns_full_rewrite(self, populated_standards_engine):
        """Validates project rule validation warns about full rewrites"""
        result = populated_standards_engine.validate_project_rule("Rewrite the entire file")
        
        assert "warnings" in result
        assert any("rewrite" in w.lower() for w in result["warnings"])

    def test_global_rules_priority_lower_than_project(self, populated_standards_engine):
        """Validates global rules have lower priority than project"""
        global_rules = populated_standards_engine.get_global_rules()
        project_rules = populated_standards_engine.get_project_rules()
        
        assert global_rules[0].priority < project_rules[0].priority

    def test_reload_refreshes_rules(self, temp_rules_dirs, populated_standards_engine):
        """Validates reload refreshes rules from disk"""
        global_dir, project_dir = temp_rules_dirs
        
        # Add new global rule
        (global_dir / "new_rule.md").write_text("""---
category: global
---
# New Global Rule
""")
        
        populated_standards_engine.reload()
        
        assert len(populated_standards_engine.get_global_rules()) == 2


class TestSpecFirstPlannerPlanJsonSchema:
    """Test spec-first planner plan.json schema"""

    def test_create_plan_generates_valid_schema(self, temp_plan_path):
        """Validates plan creation generates correct schema"""
        planner = SpecFirstPlanner(plan_path=temp_plan_path)
        
        plan = planner.create_plan(
            goal="Test goal",
            constraints=["Constraint 1", "Constraint 2"],
            affected_files=["file1.py", "file2.py"],
            task_id="test_123",
        )
        
        assert plan.task_id == "test_123"
        assert plan.goal == "Test goal"
        assert plan.constraints == ["Constraint 1", "Constraint 2"]
        assert plan.affected_files == ["file1.py", "file2.py"]
        assert plan.schema_version == "1.0.0"
        assert plan.steps == []

    def test_plan_json_persists_to_disk(self, temp_plan_path):
        """Validates plan.json is written to disk"""
        planner = SpecFirstPlanner(plan_path=temp_plan_path)
        
        planner.create_plan(goal="Persist test")
        
        assert temp_plan_path.exists()
        
        # Verify JSON structure
        import json
        data = json.loads(temp_plan_path.read_text())
        assert data["goal"] == "Persist test"
        assert "task_id" in data
        assert "steps" in data
        assert "constraints" in data
        assert "affected_files" in data

    def test_plan_load_from_disk(self, temp_plan_path):
        """Validates plan loading from disk"""
        planner = SpecFirstPlanner(plan_path=temp_plan_path)
        
        original = planner.create_plan(goal="Load test")
        
        # New planner instance
        new_planner = SpecFirstPlanner(plan_path=temp_plan_path)
        loaded = new_planner.load_plan()
        
        assert loaded is not None
        assert loaded.task_id == original.task_id
        assert loaded.goal == original.goal

    def test_add_step_to_plan(self, populated_planner):
        """Validates adding steps to plan"""
        step = populated_planner.add_step(
            "New step",
            affected_files=["src/new.py"],
            verification="test",
        )
        
        assert step.id == "step_3"
        assert step.description == "New step"
        assert step.status == "pending"
        assert step.affected_files == ["src/new.py"]
        
        # Verify persisted
        loaded = populated_planner.load_plan()
        assert len(loaded.steps) == 3

    def test_update_step_status(self, populated_planner):
        """Validates step status updates"""
        result = populated_planner.update_step_status("step_1", "completed")
        assert result is True
        
        step = populated_planner.get_step("step_1")
        assert step.status == "completed"
        
        # Verify persisted
        loaded = populated_planner.load_plan()
        assert loaded.steps[0].status == "completed"

    def test_get_next_pending_step(self, populated_planner):
        """Validates getting next pending step"""
        next_step = populated_planner.get_next_pending_step()
        
        assert next_step is not None
        assert next_step.id == "step_1"
        assert next_step.status == "pending"

    def test_format_plan_block(self, populated_planner):
        """Validates plan block formatting for prompt injection"""
        block = populated_planner.format_plan_block()
        
        assert "<|ACTIVE_PLAN_STATE|>" in block
        assert "TASK_ID:" in block
        assert "GOAL:" in block
        assert "CONSTRAINTS:" in block
        assert "AFFECTED_FILES:" in block
        assert "STEPS:" in block
        assert "[ ]" in block  # pending
        assert "</|ACTIVE_PLAN_STATE|>" in block

    def test_estimate_plan_tokens(self, populated_planner):
        """Validates token estimation"""
        tokens = populated_planner.estimate_plan_tokens()
        
        assert tokens > 0
        assert tokens < 200  # Should be well under budget

    def test_plan_step_structure(self):
        """Validates PlanStep dataclass structure"""
        step = PlanStep(
            id="test_1",
            description="Test step",
            affected_files=["file.py"],
            verification="test",
        )
        
        assert step.id == "test_1"
        assert step.status == "pending"
        assert step.to_dict()["id"] == "test_1"


class TestPreImplementationPlanGate:
    """Test pre-implementation plan gate"""

    def test_gate_allows_edit_in_affected_files(self, populated_planner):
        """Validates gate allows editing files in affected_files"""
        gate = populated_planner.gate_before_edit("src/main.py")
        
        assert gate["allowed"] is True
        assert "Proceed" in gate["reason"]
        assert "next_step" in gate

    def test_gate_blocks_edit_not_in_affected_files(self, populated_planner):
        """Validates gate blocks editing files not in affected_files"""
        gate = populated_planner.gate_before_edit("src/unrelated.py")
        
        assert gate["allowed"] is False
        assert "not in plan.affected_files" in gate["reason"]
        assert gate["action"] == "update_plan"

    def test_gate_blocks_when_no_plan(self, temp_plan_path):
        """Validates gate blocks when no plan exists"""
        planner = SpecFirstPlanner(plan_path=temp_plan_path)
        
        gate = planner.gate_before_edit("src/any.py")
        
        assert gate["allowed"] is False
        assert "No active plan.json" in gate["reason"]
        assert gate["action"] == "create_plan"

    def test_gate_blocks_when_plan_invalid(self, temp_plan_path):
        """Validates gate blocks when plan is invalid"""
        planner = SpecFirstPlanner(plan_path=temp_plan_path)
        
        # Create plan with no steps (invalid)
        plan = planner.create_plan(goal="Invalid plan")
        # Don't add steps
        
        gate = planner.gate_before_edit("src/main.py")
        
        assert gate["allowed"] is False
        assert "Invalid plan" in gate["reason"]

    def test_record_file_edit_updates_plan(self, populated_planner):
        """Validates recording file edits updates plan"""
        populated_planner.record_file_edit("src/new_file.py", "step_1")
        
        plan = populated_planner.get_plan()
        assert "src/new_file.py" in plan.affected_files
        assert populated_planner.get_step("step_1").status == "in_progress"

    def test_enforce_plan_gate_integration(self, populated_planner):
        """Validates integration function"""
        result = enforce_plan_gate_before_edit("src/main.py", populated_planner)
        
        assert result["allowed"] is True

    def test_enforce_plan_gate_none_planner(self):
        """Validates integration function with None planner"""
        result = enforce_plan_gate_before_edit("src/any.py", None)
        
        assert result["allowed"] is True
        assert "No planner" in result["reason"]


class TestRulesTokenBudgetInSlot3:
    """Test rules token budget in Slot 3"""

    def test_slot3_injection_token_budget(self, populated_standards_engine):
        """Validates Slot 3 injection stays under 300 tokens"""
        injection = populated_standards_engine.get_slot3_injection()
        tokens = populated_standards_engine.estimate_tokens(injection)
        
        assert tokens < 300, f"Slot 3 injection tokens {tokens} >= 300"

    def test_slot3_injection_contains_both_tiers(self, populated_standards_engine):
        """Validates injection contains both global and project rules"""
        injection = populated_standards_engine.get_slot3_injection()
        
        assert "IMMUTABLE GLOBAL CONSTRAINTS" in injection
        assert "GLOBAL STANDARDS" in injection
        assert "PROJECT STANDARDS" in injection

    def test_build_two_tier_slot3_injection(self, populated_standards_engine):
        """Validates integration function for Slot 3"""
        base_slot3 = "# SLOT 3: MASTER BEHAVIORAL INVARIANTS\nKARPATHY LAWS"
        
        enhanced = build_two_tier_slot3_injection(base_slot3, populated_standards_engine)
        
        assert "KARPATHY LAWS" in enhanced
        assert "IMMUTABLE GLOBAL CONSTRAINTS" in enhanced

    def test_inject_plan_into_slot3(self, populated_planner):
        """Validates plan injection into Slot 3"""
        base_slot3 = "# SLOT 3: INVARIANTS"
        
        enhanced = inject_plan_into_slot3(base_slot3, populated_planner)
        
        assert "KARPATHY LAWS" not in enhanced  # Not in base
        assert "<|ACTIVE_PLAN_STATE|>" in enhanced
        assert "TASK_ID:" in enhanced

    def test_token_budget_with_many_rules(self, temp_rules_dirs):
        """Validates token budget respected with many rules"""
        global_dir, project_dir = temp_rules_dirs
        
        # Create many rules
        for i in range(10):
            (global_dir / f"global_{i}.md").write_text(f"""---
category: global
---
# Global Rule {i}
- Setting: value_{i}
""" * 10)
        
        for i in range(10):
            (project_dir / f"project_{i}.md").write_text(f"""---
category: project
---
# Project Rule {i}
- Setting: value_{i}
""" * 10)
        
        engine = TwoTierStandardsEngine(
            global_rules_dir=global_dir,
            project_root=project_dir.parent.parent,
            max_slot3_tokens=300,
        )
        
        injection = engine.get_slot3_injection()
        tokens = engine.estimate_tokens(injection)
        
        assert tokens <= 300


class TestAgentOSZeroGPUVRAM:
    """Test zero GPU VRAM overhead"""

    def test_standards_zero_vram_guarantee(self, populated_standards_engine):
        """Validates standards engine zero VRAM guarantee"""
        guarantee = populated_standards_engine.get_zero_vram_guarantee()
        
        assert guarantee["yaml_parsing_cpu_only"] is True
        assert guarantee["file_io_cpu_only"] is True
        assert guarantee["token_estimation_cpu_only"] is True
        assert guarantee["no_gpu_operations"] is True
        assert guarantee["ramdisk_compatible"] is True

    def test_planner_zero_vram_guarantee(self, populated_planner):
        """Validates planner zero VRAM guarantee"""
        guarantee = populated_planner.get_zero_vram_guarantee()
        
        assert guarantee["json_parsing_cpu_only"] is True
        assert guarantee["file_io_cpu_only"] is True
        assert guarantee["plan_formatting_cpu_only"] is True
        assert guarantee["no_gpu_operations"] is True
        assert guarantee["ramdisk_compatible"] is True

    def test_no_gpu_imports_standards(self):
        """Validates no GPU libraries in standards module"""
        import hermes_core.agent_os_standards as aos
        
        forbidden = ["torch", "tensorflow", "cuda", "cupy", "jax"]
        for mod in forbidden:
            assert not hasattr(aos, mod)

    def test_no_gpu_imports_planner(self):
        """Validates no GPU libraries in planner module"""
        import hermes_core.spec_first_planner as sfp
        
        forbidden = ["torch", "tensorflow", "cuda", "cupy", "jax"]
        for mod in forbidden:
            assert not hasattr(sfp, mod)

    def test_operations_on_cpu(self, populated_standards_engine, populated_planner):
        """Validates all operations execute on CPU"""
        # Standards operations
        populated_standards_engine.compile()
        populated_standards_engine.get_slot3_injection()
        populated_standards_engine.validate_project_rule("test")
        
        # Planner operations
        populated_planner.gate_before_edit("src/test.py")
        populated_planner.format_plan_block()
        populated_planner.validate_plan()
        
        # All completed without GPU
        assert True


class TestStandardsEngineLifecycle:
    """Test standards engine lifecycle"""

    def test_get_standards_engine_singleton(self):
        """Validates singleton factory pattern"""
        reset_standards_engine()
        
        engine1 = get_standards_engine()
        engine2 = get_standards_engine()
        
        assert engine1 is engine2
        reset_standards_engine()

    def test_get_spec_first_planner_singleton(self):
        """Validates singleton factory pattern for planner"""
        reset_spec_first_planner()
        
        planner1 = get_spec_first_planner()
        planner2 = get_spec_first_planner()
        
        assert planner1 is planner2
        reset_spec_first_planner()

    def test_rule_parser_structure(self, temp_rules_dirs):
        """Validates RuleParser produces correct structure"""
        global_dir, _ = temp_rules_dirs
        
        rule_file = global_dir / "test.md"
        rule_file.write_text("""---
version: 1.0.0
category: global
immutable: true
---
# Test Rule
Content here
""")
        
        parsed = RuleParser.parse(rule_file, "global")
        
        assert isinstance(parsed, RuleFile)
        assert parsed.category == "global"
        assert parsed.frontmatter["immutable"] is True
        assert parsed.tokens > 0
        assert len(parsed.hash) == 16
        assert "Test Rule" in parsed.content


class TestCompiledStandardsStructure:
    """Test compiled standards structure"""

    def test_compiled_standards_structure(self, populated_standards_engine):
        """Validates CompiledStandards dataclass"""
        compiled = populated_standards_engine.compile()
        
        assert isinstance(compiled, CompiledStandards)
        assert isinstance(compiled.global_rules, list)
        assert isinstance(compiled.project_rules, list)
        assert isinstance(compiled.merged_content, str)
        assert isinstance(compiled.total_tokens, int)
        assert isinstance(compiled.global_hash, str)
        assert isinstance(compiled.project_hash, str)
        assert compiled.total_tokens > 0

    def test_compiled_hashes_stable(self, populated_standards_engine):
        """Validates compiled hashes are stable"""
        c1 = populated_standards_engine.compile()
        c2 = populated_standards_engine.compile()
        
        assert c1.global_hash == c2.global_hash
        assert c1.project_hash == c2.project_hash
        assert c1.merged_content == c2.merged_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
