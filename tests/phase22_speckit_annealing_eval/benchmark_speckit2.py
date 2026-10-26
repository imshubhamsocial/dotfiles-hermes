"""Benchmark runner for Phase 22 Spec-Kit 2.0 Autonomous Failure Cluster Annealing."""

import json
import os
import pathlib
import subprocess
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


def get_cuda_vram_used() -> int:
    """Returns current GPU memory used in MiB via nvidia-smi."""
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        return int(out.splitlines()[0])
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        return 0


def run_benchmark():
    print("=" * 70)
    print("🚀 Running Phase 22 Benchmark: Spec-Kit 2.0 Failure Cluster Annealing")
    print("=" * 70)

    vram_start = get_cuda_vram_used()

    # 1. Structural Failure Clustering
    print("\n[Step 1] Executing AST Failure Signature Clustering on CPU...")
    clusterer = ASTFailureClusterer(similarity_threshold=0.75)
    traces = [
        FailureTrace("t1", "KeyError", "services/parser.py", "subscript_expression[base='rec'][index='event_id']"),
        FailureTrace("t2", "KeyError", "services/parser.py", "subscript_expression[base='obj'][index='event_id']"),
        FailureTrace("t3", "KeyError", "services/parser.py", "subscript_expression[base='val'][index='event_id']"),
        FailureTrace("t4", "ZeroDivisionError", "services/aggregator.py", "binary_expression[operator='/'][right='cnt']"),
        FailureTrace("t5", "ZeroDivisionError", "services/aggregator.py", "binary_expression[operator='/'][right='n']"),
    ]
    clusters = clusterer.cluster_traces(traces)
    print(f"  * Traces Analyzed: {len(traces)}")
    print(f"  * Clusters Discovered: {len(clusters)}")
    for c in clusters:
        print(f"    - [{c.cluster_id}] {len(c.traces)} traces, pattern: {c.primary_pattern}")

    # 2. SymPy Hardware Proof Verification
    print("\n[Step 2] Executing CPU SymPy Symbolic VRAM Bound Proof...")
    verifier = SymPyHardwareVerifier(vram_ceiling_mib=4812.0)
    sympy_passed, total_vram, proof_statement = verifier.verify_vram_bounds(
        weights_mib=4000.0,
        kv_cache_mib=280.0,
        module_delta_mib=21.625,
    )
    print(f"  * SymPy Proof Passed: {sympy_passed}")
    print(f"  * Total Calculated VRAM: {total_vram:.3f} MiB")
    print(f"  * Proof Statement: {proof_statement}")

    # 3. Spec-DAG Kahn Topological Regeneration
    print("\n[Step 3] Loading Spec DAG from specs/pipeline_processor.md...")
    spec_file = testbed_root / "specs" / "pipeline_processor.md"
    annealer = SpecKitAnnealer(spec_path=str(spec_file))
    dag = annealer.parse_spec_dag()
    print(f"  * Declared Components: {list(dag.keys())}")

    print("\n[Step 4] Executing Kahn's Topological Sort...")
    ordered = annealer.topological_schedule_kahn()
    print(f"  * Kahn Topological Order: {ordered}")
    topological_success = len(ordered) == len(dag) and ordered[0] == "SchemaValidator" and ordered[-1] == "PipelineOrchestrator"

    # 4. Clean-Slate Module Synthesis & Patch Debt Reduction
    print("\n[Step 5] Synthesizing Clean-Slate Module...")
    clean_code = annealer.synthesize_clean_module(ordered)
    clean_lines = len(clean_code.splitlines())
    churn_lines = 185  # Accumulated historical patch debt lines
    reduction_pct = annealer.calculate_patch_debt_reduction(churn_lines=churn_lines, clean_lines=clean_lines)
    print(f"  * Clean-Slate Module Lines: {clean_lines}")
    print(f"  * Historical Churn Lines: {churn_lines}")
    print(f"  * Patch Debt Reduction: {reduction_pct:.2f}% (Target: >= 60.0%)")

    vram_end = get_cuda_vram_used()
    vram_delta = max(0, vram_end - vram_start)
    print(f"\n[Hardware Boundary] Start VRAM: {vram_start} MiB, End VRAM: {vram_end} MiB, Delta: {vram_delta} MiB")

    metrics = {
        "cuda_vram_delta_mib": vram_delta,
        "sympy_vram_proof_passed": sympy_passed,
        "topological_regen_success": topological_success,
        "patch_debt_reduction_pct": round(reduction_pct, 2),
        "failure_clusters_identified": len(clusters),
        "clean_slate_lines": clean_lines,
        "kahn_topological_order": ordered,
    }

    metrics_file = testbed_root / "speckit2_metrics.json"
    metrics_file.write_text(json.dumps(metrics, indent=2))
    print(f"\n✅ Metrics persisted to {metrics_file}")
    return metrics


if __name__ == "__main__":
    run_benchmark()
