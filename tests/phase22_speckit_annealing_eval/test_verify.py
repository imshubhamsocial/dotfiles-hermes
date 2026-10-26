"""Machine verification gate for Phase 22 Spec-Kit 2.0 Failure Cluster Annealing."""

import json
import os
import pathlib
import sys

testbed_root = pathlib.Path(__file__).resolve().parent
scenario_dir = testbed_root / "scenario"
sys.path.insert(0, str(scenario_dir))

from annealing_engine import (
    ASTFailureClusterer,
    FailureTrace,
    SpecKitAnnealer,
    SymPyHardwareVerifier,
)


def test_speckit2_metrics_and_gate():
    """Validates that speckit2_metrics.json exists and satisfies Phase 22 invariants."""
    metrics_path = testbed_root / "speckit2_metrics.json"
    assert metrics_path.exists(), f"Metrics file {metrics_path} must exist (run benchmark_speckit2.py)"

    metrics = json.loads(metrics_path.read_text())

    # Invariant 1: 0 MiB CUDA VRAM Delta (CPU SymPy & ast-grep)
    assert metrics["cuda_vram_delta_mib"] == 0, (
        f"CUDA VRAM delta must be 0, got {metrics['cuda_vram_delta_mib']} MiB"
    )

    # Invariant 2: SymPy Hardware VRAM Proof Passed (<= 4,812 MiB)
    assert metrics["sympy_vram_proof_passed"] is True, "SymPy VRAM bound proof must pass"

    # Invariant 3: Topological Spec Regeneration Success
    assert metrics["topological_regen_success"] is True, "Topological module regeneration must succeed"

    # Invariant 4: Patch Debt Reduction >= 60.0%
    assert metrics["patch_debt_reduction_pct"] >= 60.0, (
        f"Patch debt reduction must be >= 60.0%, got {metrics['patch_debt_reduction_pct']}%"
    )

    # Invariant 5: Topological Ordering verified
    order = metrics["kahn_topological_order"]
    assert order[0] == "SchemaValidator"
    assert order[-1] == "PipelineOrchestrator"


def test_live_speckit2_annealing_execution():
    """Live functional verification of Spec-Kit 2.0 annealing engine."""
    annealer = SpecKitAnnealer()
    dag = {
        "LeafA": [],
        "LeafB": [],
        "MidNode": ["LeafA", "LeafB"],
        "RootNode": ["MidNode"],
    }
    ordered = annealer.topological_schedule_kahn(dag)
    assert ordered.index("LeafA") < ordered.index("MidNode")
    assert ordered.index("LeafB") < ordered.index("MidNode")
    assert ordered.index("MidNode") < ordered.index("RootNode")

    # Verify SymPy symbolic evaluation directly
    verifier = SymPyHardwareVerifier(vram_ceiling_mib=4812.0)
    passed, total_vram, _ = verifier.verify_vram_bounds()
    assert passed is True
    assert total_vram <= 4812.0
