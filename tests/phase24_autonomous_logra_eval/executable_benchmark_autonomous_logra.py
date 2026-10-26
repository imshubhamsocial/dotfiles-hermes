#!/usr/bin/env python3
"""Benchmark runner for Phase 24 Autonomous Offline LoGRA/NoRA Weight Evolution.

Executes offline adaptation cycle on training_buffer/samples.jsonl and outputs
autonomous_logra_metrics.json.
"""

import json
import os
import pathlib
import sys

testbed_root = pathlib.Path(__file__).resolve().parent
scenario_dir = testbed_root / "scenario"
sys.path.insert(0, str(scenario_dir))

from offline_adapter_engine import OfflineEvolutionOrchestrator


def run_benchmark():
    buffer_path = scenario_dir / "training_buffer" / "samples.jsonl"
    print(f"Ingesting trajectories from: {buffer_path}")

    orchestrator = OfflineEvolutionOrchestrator(
        str(buffer_path),
        rank=64,
        d_model=2048,
        kl_budget=0.05,
    )

    metrics = orchestrator.run_offline_evolution_cycle()

    out_file = testbed_root / "autonomous_logra_metrics.json"
    out_file.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print("\n========================================================")
    print("📊 Phase 24 Offline LoGRA/NoRA Evolution Benchmark Results")
    print("========================================================")
    for k, v in metrics.items():
        print(f"  • {k}: {v}")
    print("========================================================")
    print(f"Metrics saved to: {out_file}\n")


if __name__ == "__main__":
    run_benchmark()
