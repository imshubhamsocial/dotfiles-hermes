"""Unit test suite for Phase 25 Dream-ARSI Master Omniscient Operating Kernel."""

import pytest
from arsi_kernel import (
    ArgonChallenge1_STAIR_AST,
    ArgonChallenge2_DeclarativeAttention,
    ArgonChallenge3_ProactiveSecurity_SymPy,
    ArgonChallenge4_ADK_TaskDAG,
    ArgonChallenge5_SpecKit_Annealing,
    ArgonChallenge6_DreamRSI_OfflineLoGRA,
    MasterARSIKernel,
)


def test_challenge1_stair_ast():
    c1 = ArgonChallenge1_STAIR_AST()
    code = "def compute_loss(x, y):\n    return (x - y) ** 2\n"
    res = c1.verify(code)
    assert res.passed is True
    assert res.metrics["cuda_delta_mib"] == 0.0
    assert res.metrics["indexed_symbols"] >= 1


def test_challenge2_declarative_attention():
    c2 = ArgonChallenge2_DeclarativeAttention(attractor_epsilon=0.05, max_attractor_iters=5)
    res = c2.verify()
    assert res.passed is True
    assert res.metrics["convergence_steps"] <= 5
    assert res.metrics["final_delta"] <= 0.05
    assert res.metrics["kv_cache_reuse_ratio"] >= 0.85


def test_challenge3_proactive_security_sympy():
    c3 = ArgonChallenge3_ProactiveSecurity_SymPy(vram_limit_mib=4812.0)
    res = c3.verify()
    assert res.passed is True
    assert res.metrics["injection_blocked"] is True
    assert res.metrics["active_vram_mib"] <= 4812.0


def test_challenge4_adk_taskdag():
    c4 = ArgonChallenge4_ADK_TaskDAG()
    res = c4.verify()
    assert res.passed is True
    assert res.metrics["cycle_count"] == 0
    assert len(res.metrics["dag_order"]) == 4


def test_challenge5_speckit_annealing():
    c5 = ArgonChallenge5_SpecKit_Annealing()
    res = c5.verify()
    assert res.passed is True
    assert res.metrics["residual_error_rate"] == 0.0


def test_challenge6_dream_rsi_logra_tme():
    c6 = ArgonChallenge6_DreamRSI_OfflineLoGRA()
    res = c6.verify()
    assert res.passed is True
    assert res.metrics["quiescent_vram_mib"] <= 650.0
    assert res.metrics["nora_frobenius_norm"] == 1.0
    assert res.metrics["post_resume_mtp_tok_per_sec"] >= 42.4
    assert res.metrics["dream_call_reduction_factor"] >= 2.0


def test_master_arsi_kernel_full_gauntlet():
    kernel = MasterARSIKernel()
    report = kernel.execute_master_evaluation()
    assert report["all_14_phases_certified"] is True
    assert report["peak_online_vram_mib"] <= 4812.0
    assert report["zero_spoon_feeding_verified"] is True
    assert report["argon_gauntlet_challenges_passed"] == 6
    assert len(report["challenges"]) == 6
    assert all(c["passed"] for c in report["challenges"])
