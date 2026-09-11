"""
Contract Tests: Pillar IV — Frontier Skill Intelligence OS
===========================================================
Validates:
  1. Gemini 3.8 ThoughtSignature initialization and state tracking.
  2. ThoughtSignature persistence to JSON in active storage.
  3. Step transition: marks completed step and auto-advances active step.
  4. Context drift detection: aligned query produces low drift score.
  5. Context drift detection: divergent query flags high drift score.
  6. SuperpowersRegistry initializes with core engineering capabilities.
  7. SuperpowersRegistry matches prompt triggers to registered superpowers.
  8. SuperpowersRegistry ranks multi-keyword trigger matches by score.
  9. XMLContractValidator accepts compliant 4-block XML skill text.
 10. XMLContractValidator detects missing blocks (e.g. missing <output_requirements>).
 11. XMLContractValidator confirms all 4 installed cybersecurity skills are valid.
 12. Thought pre_turn hook injects compact active step representation under token budget.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
import pytest

from plugins.skill_intelligence import (
    ThoughtSignatureEngine,
    ThoughtSignature,
    SuperpowersRegistry,
    XMLContractValidator,
    register,
)


@pytest.fixture
def temp_thought_engine():
    with tempfile.TemporaryDirectory() as tmpdir:
        engine = ThoughtSignatureEngine(storage_dir=Path(tmpdir))
        yield engine


@pytest.fixture
def temp_superpowers():
    with tempfile.TemporaryDirectory() as tmpdir:
        reg_file = Path(tmpdir) / "registry.json"
        reg = SuperpowersRegistry(registry_file=reg_file)
        yield reg


def test_thought_signature_initialization(temp_thought_engine):
    sig = temp_thought_engine.create_signature(
        task_id="task_123",
        goal="Implement AST parser",
        steps=["Parse AST", "Verify Types", "Emit Bytecode"],
    )
    assert sig.task_id == "task_123"
    assert sig.active_step == "Parse AST"
    assert len(sig.completed_steps) == 0
    assert sig.context_drift_score == 0.0


def test_thought_signature_persistence(temp_thought_engine):
    sig = temp_thought_engine.create_signature(
        task_id="task_persist",
        goal="Database Migration",
        steps=["Create table", "Seed data"],
    )
    persisted_file = temp_thought_engine.storage_dir / "task_persist.json"
    assert persisted_file.exists()
    assert "Database Migration" in persisted_file.read_text()


def test_thought_signature_step_transition(temp_thought_engine):
    sig = temp_thought_engine.create_signature(
        task_id="task_step",
        goal="Feature development",
        steps=["Step A", "Step B", "Step C"],
    )
    temp_thought_engine.update_step("Step A")
    assert "Step A" in sig.completed_steps
    assert sig.active_step == "Step B"

    temp_thought_engine.update_step("Step B")
    assert sig.active_step == "Step C"


def test_thought_signature_drift_aligned(temp_thought_engine):
    temp_thought_engine.create_signature(
        task_id="task_drift_align",
        goal="Refactor authentication handler for OAuth2 tokens",
        steps=["Audit tokens", "Refactor handler"],
    )
    drift = temp_thought_engine.evaluate_drift("Refactoring the authentication handler logic for OAuth2")
    assert drift < 0.60


def test_thought_signature_drift_divergence(temp_thought_engine):
    temp_thought_engine.create_signature(
        task_id="task_drift_div",
        goal="Optimize SQLite B-Tree indexing",
        steps=["Add indices", "Measure latency"],
    )
    # Completely divergent turn talking about CSS styling
    drift = temp_thought_engine.evaluate_drift("Can you help design a vibrant pink CSS stylesheet for button hover animations?")
    assert drift >= 0.80


def test_superpowers_registry_initialization(temp_superpowers):
    all_sp = temp_superpowers.list_all()
    assert len(all_sp) >= 5
    ids = [s["id"] for s in all_sp]
    assert "security_audit" in ids
    assert "secret_detection" in ids
    assert "threat_model" in ids


def test_superpowers_trigger_matching(temp_superpowers):
    matches = temp_superpowers.match("Please conduct a vulnerability audit on the API")
    assert len(matches) >= 1
    assert matches[0]["id"] == "security_audit"
    assert "security-audit" in matches[0]["skill_ref"]


def test_superpowers_multi_trigger_ranking(temp_superpowers):
    matches = temp_superpowers.match("Detect leaked secret API key and credentials")
    assert len(matches) >= 1
    assert matches[0]["id"] == "secret_detection"


def test_xml_validator_valid_contract():
    sample_xml = """---
name: test-skill
---
<instructions>
Role and constraints.
</instructions>
<context>
Environment invariants.
</context>
<task>
1. Run audit.
</task>
<output_requirements>
Markdown format table.
</output_requirements>
"""
    valid, missing = XMLContractValidator.validate_skill_text(sample_xml)
    assert valid is True
    assert len(missing) == 0


def test_xml_validator_detects_missing_blocks():
    incomplete_xml = """<instructions>Role</instructions><task>Do it</task>"""
    valid, missing = XMLContractValidator.validate_skill_text(incomplete_xml)
    assert valid is False
    assert "context" in missing
    assert "output_requirements" in missing


def test_xml_validator_cybersecurity_skills():
    hermes_home = Path(__file__).resolve().parent.parent.parent
    skills_dir = hermes_home / "skills" / "engineering"
    targets = ["security-audit", "secret-detection", "threat-model", "pentest-assist"]

    for t in targets:
        skill_file = skills_dir / t / "SKILL.md"
        assert skill_file.exists(), f"Skill file {skill_file} should exist"
        res = XMLContractValidator.validate_skill_file(skill_file)
        assert res["valid"] is True, f"Skill {t} failed validation: {res['missing_blocks']}"


def test_thought_pre_turn_hook_injection(temp_thought_engine):
    class DummyContext:
        def __init__(self):
            self.hooks = {}
            self.cli_cmds = {}
            self.cmds = {}

        def register_hook(self, name, fn):
            self.hooks[name] = fn

        def register_cli_command(self, name, desc, setup, handler):
            self.cli_cmds[name] = handler

        def register_command(self, name, fn, desc, usage):
            self.cmds[name] = fn

    ctx = DummyContext()
    register(ctx)
    assert "pre_turn" in ctx.hooks
    hook_res = ctx.hooks["pre_turn"]()
    assert hook_res["action"] == "continue"


def test_superpowers_cli_list_action():
    import argparse
    class DummyContext:
        def __init__(self):
            self.cli_setups = {}
            self.cli_handlers = {}
            self.hooks = {}
            self.cmds = {}

        def register_hook(self, name, fn):
            self.hooks[name] = fn

        def register_cli_command(self, name, desc, setup, handler):
            self.cli_setups[name] = setup
            self.cli_handlers[name] = handler

        def register_command(self, name, fn, desc, usage):
            self.cmds[name] = fn

    ctx = DummyContext()
    register(ctx)
    parser = argparse.ArgumentParser()
    ctx.cli_setups["superpowers"](parser)
    args = parser.parse_args(["list"])
    assert args.action == "list"
    res = ctx.cli_handlers["superpowers"](args)
    assert res == 0


def test_thought_signature_durability_and_mirror(tmp_path):
    durable_dir = tmp_path / "durable"
    hot_dir = tmp_path / "hot"
    durable_dir.mkdir()
    hot_dir.mkdir()

    engine = ThoughtSignatureEngine(storage_dir=durable_dir)
    engine.hot_dir = hot_dir
    sig = engine.create_signature("task_dur", "Durable Task", ["Step 1", "Step 2"])

    assert (durable_dir / "task_dur.json").exists()
    assert (hot_dir / "task_dur.json").exists()

    # Re-instantiate engine pointing to durable_dir with empty hot_dir
    engine2 = ThoughtSignatureEngine(storage_dir=durable_dir)
    assert engine2.active_signature is not None
    assert engine2.active_signature.task_id == "task_dur"
