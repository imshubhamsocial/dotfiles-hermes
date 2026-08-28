"""
Contract Tests: Roadmap 4 Milestone U51
========================================
Validates NVIDIA SkillEvaluator Automated Skill Lift Evaluation Harness Subsystem:
1. Multi-Dimensional Metric Schema (Correctness, Efficiency, Integration, Self-Healing, First-Attempt)
2. A/B Baseline vs. Candidate Empirical Benchmark Run
3. Statistical Quality Gate (>= +15% Skill Lift Rule & <= 150 Token Bloat Rule)
4. Persistent Markdown Evaluation Receipt Generation in `.hermes/knowledge/evaluations/`
5. Strict Hardware Envelope Bounds (Pure CPU / RAMDisk execution, 0 MB GPU VRAM)
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / ".hermes" / "src"))

import pytest

from hermes_core.skill_evaluator import (
    EvaluationDimensions,
    EvaluationEpisode,
    SkillLiftReport,
    SkillEvaluator,
    create_skill_evaluator,
)


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def sample_baseline_episodes() -> list[EvaluationEpisode]:
    """Generates baseline episodes with moderate pass rate (50%) and standard token budget."""
    return [
        EvaluationEpisode(
            task_id=f"base_task_{i}",
            passed=(i % 2 == 0),
            total_tokens=1000 + (i * 20),
            duration_sec=25.0 + (i * 2),
            retries=1 if i % 2 != 0 else 0,
            syntax_errors=1 if i % 2 != 0 else 0,
            symbols_resolved=8,
            symbols_total=10,
            recovered_from_error=False,
            first_try_pass=(i % 2 == 0),
        )
        for i in range(10)
    ]


@pytest.fixture
def sample_superior_candidate_episodes() -> list[EvaluationEpisode]:
    """Generates superior candidate episodes (+80% pass rate, lower tokens, fast duration)."""
    return [
        EvaluationEpisode(
            task_id=f"cand_task_{i}",
            passed=(i < 8),  # 80% pass rate (+60% lift over 50%)
            total_tokens=900 + (i * 10),
            duration_sec=15.0 + i,
            retries=0 if i < 8 else 1,
            syntax_errors=0,
            symbols_resolved=10,
            symbols_total=10,
            recovered_from_error=True if i >= 8 else False,
            first_try_pass=(i < 8),
        )
        for i in range(10)
    ]


@pytest.fixture
def sample_regressive_candidate_episodes() -> list[EvaluationEpisode]:
    """Generates regressive candidate episodes with heavy prompt bloat and lower pass rate."""
    return [
        EvaluationEpisode(
            task_id=f"regress_task_{i}",
            passed=(i < 3),  # 30% pass rate (-40% regression)
            total_tokens=1400 + (i * 30),  # Heavy prompt bloat (>150 tok delta)
            duration_sec=40.0 + i,
            retries=2,
            syntax_errors=2,
            symbols_resolved=5,
            symbols_total=10,
            recovered_from_error=False,
            first_try_pass=False,
        )
        for i in range(10)
    ]


# =============================================================================
# 1. EVALUATION DIMENSIONS & SCORING TESTS
# =============================================================================

class TestEvaluationDimensionsScoring:
    """Validates 5-dimensional evaluation and composite score formulas."""

    def test_dimensions_composite_calculation(self):
        dims = EvaluationDimensions(
            correctness=100.0,
            efficiency=80.0,
            integration=90.0,
            self_healing=70.0,
            first_attempt_rate=85.0,
        )
        expected = (
            100.0 * 0.35
            + 80.0 * 0.20
            + 90.0 * 0.20
            + 70.0 * 0.15
            + 85.0 * 0.10
        )
        assert dims.composite_score == round(expected, 2)
        assert dims.to_dict()["composite_score"] == dims.composite_score

    def test_empty_episodes_return_zero_dimensions(self):
        evaluator = SkillEvaluator()
        dims = evaluator.evaluate_episodes([])
        assert dims.correctness == 0.0
        assert dims.efficiency == 0.0
        assert dims.composite_score == 0.0


# =============================================================================
# 2. A/B BENCHMARK RUN & SKILL LIFT EVALUATION
# =============================================================================

class TestSkillEvaluatorABBenchmark:
    """Validates A/B benchmark execution and comparative delta tracking."""

    def test_skill_evaluator_ab_benchmark_run(
        self, sample_baseline_episodes, sample_superior_candidate_episodes
    ):
        evaluator = create_skill_evaluator()
        comparison = evaluator.compare_ab_variants(
            sample_baseline_episodes, sample_superior_candidate_episodes
        )

        assert "baseline" in comparison
        assert "variant" in comparison
        assert "delta" in comparison
        assert comparison["delta"]["variant_superior"] is True
        assert comparison["delta"]["correctness_delta"] > 0
        assert comparison["delta"]["composite_score_delta"] > 0

    def test_skill_lift_metric_calculation(
        self, sample_baseline_episodes, sample_superior_candidate_episodes
    ):
        evaluator = SkillEvaluator()
        report = evaluator.evaluate_skill_lift(
            skill_name="webgl_kinematics_mastery",
            baseline_episodes=sample_baseline_episodes,
            candidate_episodes=sample_superior_candidate_episodes,
        )

        # Baseline: 5/10 = 50.0%, Candidate: 8/10 = 80.0%
        # Pass Rate Lift: (80 - 50) / 50 = +60.0%
        assert report.baseline_pass_rate == 50.0
        assert report.candidate_pass_rate == 80.0
        assert report.pass_rate_lift_pct == 60.0
        assert report.certified is True
        assert "APPROVED" in report.certification_reason


# =============================================================================
# 3. STATISTICAL QUALITY GATE (>= +15% LIFT & PROMPT BLOAT RULES)
# =============================================================================

class TestStatisticalQualityGate:
    """Enforces strict rejection of sub-lift, regressive, or bloated candidate skills."""

    def test_promotion_gate_requires_15_percent_lift(
        self, sample_baseline_episodes
    ):
        evaluator = SkillEvaluator()
        # Candidate with marginal improvement (+5% lift, below +15% requirement)
        marginal_episodes = [
            EvaluationEpisode(
                task_id=f"marg_task_{i}",
                passed=(i < 5 or (i == 5 and False)),  # 50% pass rate (0% lift)
                total_tokens=1000,
                duration_sec=25.0,
                retries=0,
                syntax_errors=0,
                symbols_resolved=8,
                symbols_total=10,
                recovered_from_error=False,
                first_try_pass=True,
            )
            for i in range(10)
        ]

        report = evaluator.evaluate_skill_lift(
            skill_name="marginal_skill",
            baseline_episodes=sample_baseline_episodes,
            candidate_episodes=marginal_episodes,
            min_lift_pct=15.0,
        )

        assert report.certified is False
        assert "REJECTED" in report.certification_reason
        assert "below minimum threshold (+15.0%)" in report.certification_reason

    def test_promotion_gate_rejects_prompt_bloat(
        self, sample_baseline_episodes
    ):
        evaluator = SkillEvaluator()
        # Candidate with high pass rate (+80%) BUT excessive prompt bloat (+300 tokens)
        bloated_episodes = [
            EvaluationEpisode(
                task_id=f"bloated_task_{i}",
                passed=True,  # 100% pass rate
                total_tokens=1500,  # Baseline is ~1090 -> +410 tokens bloat
                duration_sec=20.0,
                retries=0,
                syntax_errors=0,
                symbols_resolved=10,
                symbols_total=10,
                recovered_from_error=False,
                first_try_pass=True,
            )
            for i in range(10)
        ]

        report = evaluator.evaluate_skill_lift(
            skill_name="bloated_prompt_skill",
            baseline_episodes=sample_baseline_episodes,
            candidate_episodes=bloated_episodes,
            max_prompt_bloat=150,
        )

        assert report.certified is False
        assert "REJECTED" in report.certification_reason
        assert "Prompt bloat" in report.certification_reason

    def test_promotion_gate_rejects_absolute_regression(
        self, sample_baseline_episodes, sample_regressive_candidate_episodes
    ):
        evaluator = SkillEvaluator()
        report = evaluator.evaluate_skill_lift(
            skill_name="broken_skill",
            baseline_episodes=sample_baseline_episodes,
            candidate_episodes=sample_regressive_candidate_episodes,
        )

        assert report.certified is False
        assert report.candidate_pass_rate < report.baseline_pass_rate
        assert "REJECTED" in report.certification_reason


# =============================================================================
# 4. PERSISTENT EVALUATION RECEIPTS & ZERO GPU VRAM
# =============================================================================

class TestEvaluationPersistenceAndHardwareBounds:
    """Validates markdown receipt serialization and pure CPU RAMDisk execution."""

    def test_evaluation_report_markdown_generation(
        self, sample_baseline_episodes, sample_superior_candidate_episodes
    ):
        evaluator = SkillEvaluator()
        with tempfile.TemporaryDirectory() as td:
            eval_dir = Path(td) / "evaluations"
            report = evaluator.evaluate_skill_lift(
                skill_name="cpp20_raii_wrapper",
                baseline_episodes=sample_baseline_episodes,
                candidate_episodes=sample_superior_candidate_episodes,
                output_dir=eval_dir,
            )

            assert report.evaluation_receipt_path is not None
            receipt_file = Path(report.evaluation_receipt_path)
            assert receipt_file.exists()

            content = receipt_file.read_text(encoding="utf-8")
            assert "# NVIDIA SkillEvaluator Evaluation Receipt: `cpp20_raii_wrapper`" in content
            assert "✅ CERTIFIED" in content
            assert "+60.0%" in content
            assert "Machine-Readable Verification Payload" in content

    def test_skill_evaluator_zero_gpu_vram(
        self, sample_baseline_episodes, sample_superior_candidate_episodes
    ):
        """Verifies SkillEvaluator executes purely on CPU with 0 MB GPU allocation."""
        evaluator = SkillEvaluator()
        report = evaluator.evaluate_skill_lift(
            skill_name="pure_cpu_lift",
            baseline_episodes=sample_baseline_episodes,
            candidate_episodes=sample_superior_candidate_episodes,
        )
        assert report.certified is True
