"""Looped Prefill & Latent Thought Attractor Solver (Phase 19 / Layer 4)."""

import math
from typing import Any


class LatentAttractorSolver:
    """Deliberates over high-entropy problem states using recurrent latent representations."""

    def __init__(self, dim: int = 32, max_loops: int = 6, epsilon: float = 0.01):
        self.dim = dim
        self.max_loops = max_loops
        self.epsilon = epsilon
        # Contraction mapping weights for fixed-point attractor (Lipschitz constant < 1)
        raw_weights = [[(math.cos((i - j) * 0.5)) for j in range(dim)] for i in range(dim)]
        frob_norm = math.sqrt(sum(raw_weights[i][j] ** 2 for i in range(dim) for j in range(dim)))
        scale = 0.20 / frob_norm
        self.weights = [[raw_weights[i][j] * scale for j in range(dim)] for i in range(dim)]

    def _layer_norm(self, vec: list[float]) -> list[float]:
        """Applies layer normalization to a vector."""
        mean = sum(vec) / len(vec)
        variance = sum((x - mean) ** 2 for x in vec) / len(vec)
        std = math.sqrt(variance + 1e-5)
        return [(x - mean) / std for x in vec]

    def _recurrent_step(self, h: list[float], eta: float = 0.8) -> list[float]:
        """Applies contractive attractor update: h <- (1 - eta)*h + eta*tanh(W h)."""
        out = [0.0] * self.dim
        for i in range(self.dim):
            linear_sum = sum(self.weights[i][j] * h[j] for j in range(self.dim))
            out[i] = (1.0 - eta) * h[i] + eta * math.tanh(linear_sum)
        return out

    def _vector_norm_diff(self, v1: list[float], v2: list[float]) -> float:
        """Calculates Euclidean L2 norm difference between two latent vectors."""
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(v1, v2)))

    def deliberate(self, initial_latent: list[float], entropy: float = 0.8) -> tuple[list[float], int, bool, float]:
        """Iterates over latent hidden state until attractor convergence or max_loops is reached.

        Returns: (final_latent, steps_taken, converged, residual_diff)
        """
        curr = list(initial_latent)
        steps = 0
        converged = False
        diff = 1.0

        for step in range(1, self.max_loops + 1):
            next_h = self._recurrent_step(curr)
            diff = self._vector_norm_diff(next_h, curr)
            curr = next_h
            steps = step

            if diff < self.epsilon:
                converged = True
                break

        return curr, steps, converged, diff

    def evaluate_constraint_graph(self, graph_entropy: float, initial_latent: list[float]) -> dict[str, Any]:
        """Evaluates whether the latent state solves a constraint graph with given entropy."""
        final_latent, steps, converged, diff = self.deliberate(initial_latent, entropy=graph_entropy)

        # High entropy problem requires stabilized latent attractor to satisfy constraints
        energy = sum(abs(x) for x in final_latent) / len(final_latent)
        if graph_entropy > 0.5:
            # If entropy is high, success requires convergence (residual diff < epsilon)
            success = converged and (diff < self.epsilon)
        else:
            success = converged or (steps <= 3)

        return {
            "success": success,
            "steps": steps,
            "converged": converged,
            "residual_diff": diff,
            "final_energy": energy,
        }
