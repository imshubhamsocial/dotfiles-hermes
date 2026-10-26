"""Unit tests for LoGRAAligner (Phase 17)."""

import numpy as np
import pytest
from logra_aligner import LoGRAAligner


def test_nora_frobenius_norm_initialization():
    aligner = LoGRAAligner(rank=64, d_model=2048)
    a_matrix, final_norm = aligner.initialize_nora_down_proj(rank=64, d_model=2048, seed=42)

    assert a_matrix.shape == (64, 2048)
    assert abs(final_norm - 1.0) < 1e-6, f"Expected Frobenius norm 1.0, got {final_norm}"


def test_logra_gradient_projection():
    aligner = LoGRAAligner(rank=64, d_model=2048)
    rng = np.random.default_rng(101)
    grad = rng.standard_normal((2048, 2048), dtype=np.float32)

    projected = aligner.project_logra_gradient(grad, seed=42)
    assert projected.shape == (2048, 2048)
    assert not np.allclose(projected, 0.0)


def test_kl_budget_verification():
    aligner = LoGRAAligner(kl_budget=0.05)
    assert aligner.validate_kl_budget(0.012) is True
    assert aligner.validate_kl_budget(0.049) is True
    assert aligner.validate_kl_budget(0.051) is False
