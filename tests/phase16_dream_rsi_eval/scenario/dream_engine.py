"""DreamRSI Replay Simulator & Counterfactual Branch Engine (Phase 16)."""

import hashlib
import json
import os
import pathlib
from typing import Any


class DreamReplayEngine:
    """Simulates offline trajectory replay and counterfactual branch pruning."""

    def __init__(self, cache_dir: str = ".hermes/cache/dream_worlds"):
        self.cache_dir = pathlib.Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def compute_task_hash(self, trace: list[dict[str, Any]]) -> str:
        """Computes a deterministic hash of the execution trajectory."""
        raw = json.dumps(trace, sort_keys=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def simulate_counterfactual_pruning(
        self, trace: list[dict[str, Any]]
    ) -> tuple[float, dict[str, Any]]:
        """Simulates counterfactual branch pruning based on Two-Strike rule.

        Returns:
            (reduction_ratio, tree_dict)
            reduction_ratio = baseline_calls / pruned_calls
        """
        baseline_calls = len(trace)
        if baseline_calls == 0:
            return 1.0, {"nodes": [], "reduction_ratio": 1.0}

        pruned_nodes = []
        consecutive_failures = 0
        pruning_active = False

        for node in trace:
            exit_code = node.get("pytest_exit_code", 0)
            if pruning_active:
                continue

            pruned_nodes.append(node)
            if exit_code != 0:
                consecutive_failures += 1
                if consecutive_failures >= 2:
                    # Two consecutive failures triggered: prune rest of dead branch
                    pruning_active = True
            else:
                consecutive_failures = 0

        pruned_calls = len(pruned_nodes)
        reduction_ratio = baseline_calls / max(pruned_calls, 1)

        task_hash = self.compute_task_hash(trace)
        tree_dict = {
            "task_hash": task_hash,
            "baseline_calls": baseline_calls,
            "pruned_calls": pruned_calls,
            "reduction_ratio": reduction_ratio,
            "nodes": pruned_nodes,
        }
        cache_file = self.cache_dir / f"{task_hash}.json"
        cache_file.write_text(json.dumps(tree_dict, indent=2), encoding="utf-8")
        return reduction_ratio, tree_dict
