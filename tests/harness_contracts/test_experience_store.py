"""
Contract Spike: Phase 6 Living Experience Store & Metacognitive Flywheel
========================================================================
Tests episodic recording, compute waste detection, negative constraint
generation, playbook generation, and prompt memory synthesis.
"""

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import pytest

from hermes_core.experience_store import (
    EpisodeRecord,
    ExperienceStore,
    create_experience_store,
)


def test_experience_store_record_and_persistence():
    with tempfile.TemporaryDirectory() as td:
        db_p = Path(td) / "exp.json"
        store = create_experience_store(db_path=db_p)
        
        ep = store.record_episode(
            episode_id="ep_001",
            task_description="Build fluid solver",
            subsystem="fluid_dynamics",
            tool_calls=[{"name": "write_file", "args": {}}],
            outcome="SUCCESS",
            token_usage=350,
            duration_sec=14.5,
            error_traces=[],
        )
        assert ep.episode_id == "ep_001"
        assert db_p.exists()
        
        # Reload in new instance
        store2 = create_experience_store(db_path=db_p)
        assert len(store2.episodes) == 1
        assert store2.episodes[0].task_description == "Build fluid solver"


def test_compute_waste_detection():
    with tempfile.TemporaryDirectory() as td:
        db_p = Path(td) / "exp_waste.json"
        store = create_experience_store(db_path=db_p)
        
        # Episode with redundant sequential tool calls and token bloat
        store.record_episode(
            episode_id="ep_waste_1",
            task_description="Debug broken scene",
            subsystem="debug",
            tool_calls=[
                {"name": "read_file", "args": {}},
                {"name": "read_file", "args": {}},
            ],
            outcome="FAILURE",
            token_usage=1450,
            duration_sec=55.0,
            error_traces=["SyntaxError: Unexpected token '}'"],
        )
        
        warnings = store.detect_compute_waste()
        assert len(warnings) >= 2
        warning_types = [w["type"] for w in warnings]
        assert "REDUNDANT_SEQUENTIAL_TOOL_CALL" in warning_types
        assert "HIGH_TOKEN_CONSUMPTION" in warning_types


def test_negative_constraints_and_prompt_injection():
    with tempfile.TemporaryDirectory() as td:
        db_p = Path(td) / "exp_rules.json"
        store = create_experience_store(db_path=db_p)
        
        store.record_episode(
            episode_id="ep_fail",
            task_description="Patch three.js scene",
            subsystem="graphics",
            tool_calls=[],
            outcome="FAILURE",
            token_usage=500,
            duration_sec=20.0,
            error_traces=["Identifier 'raycaster' has already been declared (duplicate declaration)"],
        )
        
        constraints = store.generate_negative_constraints()
        assert len(constraints) >= 1
        assert any("global scope" in c.lower() or "namespace" in c.lower() for c in constraints)
        
        prompt_injection = store.get_context_injection_prompt("Build boids simulation", max_tokens=150)
        assert "[Living Experience Memory & Constraints]" in prompt_injection
        assert "CONSTRAINT:" in prompt_injection
