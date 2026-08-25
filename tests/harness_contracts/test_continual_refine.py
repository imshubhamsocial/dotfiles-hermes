"""
Contract Spike: Phase 9 Continual Harness & Automated /refine Loop
==================================================================
Tests post-execution trajectory evaluation, rule extraction,
and memory refinement without base prompt drift.
"""

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import pytest

from hermes_core.experience_store import create_experience_store
from hermes_core.continual_refine import (
    ContinualRefineLoop,
    RefineVerdict,
    create_continual_refine_loop,
)


def test_continual_refine_loop_on_failure_and_success():
    with tempfile.TemporaryDirectory() as td:
        exp_store = create_experience_store(db_path=Path(td) / "exp.json")
        refine_loop = create_continual_refine_loop(experience_store=exp_store)
        
        # Turn 1: Failure with syntax error
        v1 = refine_loop.refine_turn(
            task_id="t_sub_1",
            task_description="Build mesh geometry",
            tool_calls=[{"name": "patch_file"}],
            outcome="FAILURE",
            token_usage=600,
            duration_sec=18.0,
            error_traces=["SyntaxError: Unexpected token '}' (unclosed brace)"],
        )
        assert not v1.passed
        assert len(v1.new_negative_constraints) >= 1
        assert any("brace" in c.lower() for c in v1.new_negative_constraints)
        
        # Turn 2: Success on repair
        v2 = refine_loop.refine_turn(
            task_id="t_sub_2",
            task_description="Repair mesh geometry",
            tool_calls=[{"name": "patch_file"}],
            outcome="SUCCESS",
            token_usage=280,
            duration_sec=8.5,
            error_traces=[],
        )
        assert v2.passed
        assert len(exp_store.episodes) == 2
