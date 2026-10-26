"""LoGRA & NoRA Parameter Alignment Module (Phase 17)."""

import math

import numpy as np


class LoGRAAligner:
    """Manages low-rank gradient random approximation and Frobenius-normalized NoRA init."""

    def __init__(self, rank: int = 64, d_model: int = 2048, kl_budget: float = 0.05):
        self.rank = rank
        self.d_model = d_model
        self.kl_budget = kl_budget

    def compute_frobenius_norm(self, matrix: np.ndarray) -> float:
        """Computes the Frobenius norm of a 2D matrix."""
        return float(np.linalg.norm(matrix, "fro"))

    def initialize_nora_down_proj(self, rank: int = 64, d_model: int = 2048, seed: int = 42) -> tuple[np.ndarray, float]:
        """Initializes the down-projection matrix A with Frobenius normalization.

        NoRA requires ||A||_F == 1.0 at initialization to prevent gradient
        instability and catastrophic forgetting of distilled base weights.

        Returns:
            (normalized_matrix_A, frobenius_norm)
        """
        rng = np.random.default_rng(seed)
        a_matrix = rng.standard_normal((rank, d_model), dtype=np.float32)

        # Frobenius normalization: A <- A / ||A||_F
        f_norm = self.compute_frobenius_norm(a_matrix)
        normalized_a = a_matrix / f_norm
        final_norm = self.compute_frobenius_norm(normalized_a)
        return normalized_a, final_norm

    def project_logra_gradient(self, grad: np.ndarray, seed: int = 42) -> np.ndarray:
        """Projects gradient on-the-fly via rank-r random Gaussian matrix P.

        Delta_W = P * (P^T * grad)
        Avoids materializing dense gradient / Adam optimizer tensors.
        """
        d = grad.shape[0]
        rng = np.random.default_rng(seed)
        # Random Gaussian projection matrix P: d x r
        p_matrix = rng.standard_normal((d, self.rank), dtype=np.float32) / math.sqrt(self.rank)

        # Low-rank projection: P @ (P.T @ grad)
        projected = p_matrix @ (p_matrix.T @ grad)
        return projected

    def validate_kl_budget(self, kl_drift: float) -> bool:
        """Validates that policy drift respects the maximum KL threshold."""
        return bool(kl_drift <= self.kl_budget)
