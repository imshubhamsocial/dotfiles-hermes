"""Benchmark and Verification Script for Phase 17 LoGRA/NoRA TTC Evolution."""

import json
import os
import pathlib
import sys

testbed_root = pathlib.Path(__file__).resolve().parent
scripts_dir = testbed_root / "scripts"
scenario_dir = testbed_root / "scenario"
sys.path.insert(0, str(testbed_root))
sys.path.insert(0, str(scripts_dir))
sys.path.insert(0, str(scenario_dir))

from hibernate_train_mtp import execute_hibernate_training


def run_benchmark():
    output_file = testbed_root / "training_telemetry.json"
    telemetry = execute_hibernate_training(str(output_file))

    assert telemetry["peak_total_vram_mib"] <= 4812.0
    assert telemetry["nora_frobenius_norm_init"] == 1.0
    assert telemetry["kl_budget_respected"] is True
    assert telemetry["post_resume_mtp_tok_per_sec"] >= 39.7

    print("Phase 17 benchmark passed all criteria.")
    return telemetry


if __name__ == "__main__":
    run_benchmark()
