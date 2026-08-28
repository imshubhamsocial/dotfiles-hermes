"""
Contract Spike: Phase 5 Skill Evaluator & Multi-Dimensional Scoring
===================================================================
Tests multi-dimensional evaluation (Correctness, Efficiency, Integration,
Self-Healing, First-Attempt Rate) and A/B variant comparison.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / ".hermes" / "src"))

import pytest

from hermes_core.skill_evaluator import (
    EvaluationDimensions,
    EvaluationEpisode,
    SkillEvaluator,
    create_skill_evaluator,
)


def test_evaluation_dimensions_composite_scoring():
    dims = EvaluationDimensions(
        correctness=90.0,
        efficiency=80.0,
        integration=85.0,
        self_healing=75.0,
        first_attempt_rate=70.0,
    )
    score = dims.composite_score
    assert 75.0 <= score <= 90.0
    
    d = dims.to_dict()
    assert "composite_score" in d
    assert d["correctness"] == 90.0


def test_skill_evaluator_episode_scoring():
    episodes = [
        EvaluationEpisode(
            task_id="t1",
            passed=True,
            total_tokens=400,
            duration_sec=12.0,
            retries=0,
            syntax_errors=0,
            symbols_resolved=10,
            symbols_total=10,
            recovered_from_error=False,
            first_try_pass=True,
        ),
        EvaluationEpisode(
            task_id="t2",
            passed=True,
            total_tokens=650,
            duration_sec=20.0,
            retries=1,
            syntax_errors=1,
            symbols_resolved=8,
            symbols_total=10,
            recovered_from_error=True,
            first_try_pass=False,
        ),
    ]
    
    evaluator = create_skill_evaluator()
    res = evaluator.evaluate_episodes(episodes)
    assert res.correctness == 85.0
    assert res.integration == 90.0
    assert res.self_healing == 100.0  # 1 errored, 1 recovered
    assert res.first_attempt_rate == 50.0  # 1 out of 2


def test_ab_variant_comparison():
    base_episodes = [
        EvaluationEpisode(
            task_id="b1",
            passed=False,
            total_tokens=1200,
            duration_sec=45.0,
            retries=3,
            syntax_errors=2,
            symbols_resolved=4,
            symbols_total=10,
            recovered_from_error=False,
            first_try_pass=False,
        )
    ]
    
    variant_episodes = [
        EvaluationEpisode(
            task_id="v1",
            passed=True,
            total_tokens=350,
            duration_sec=10.0,
            retries=0,
            syntax_errors=0,
            symbols_resolved=10,
            symbols_total=10,
            recovered_from_error=False,
            first_try_pass=True,
        )
    ]
    
    comp = SkillEvaluator.compare_ab_variants(base_episodes, variant_episodes)
    assert comp["delta"]["variant_superior"] is True
    assert comp["delta"]["correctness_delta"] > 0
    assert comp["delta"]["efficiency_delta"] > 0
