#!/usr/bin/env python3
"""Benchmark runner for Phase 25: Dream-ARSI Master Omniscient Parity."""

import json
import pathlib
import sys

# Ensure scenario is importable
scenario_dir = pathlib.Path(__file__).resolve().parent / "scenario"
sys.path.insert(0, str(scenario_dir))

from arsi_kernel import MasterARSIKernel


def main() -> int:
    print("=" * 70)
    print("🚀 Executing Phase 25 Dream-ARSI Master Omniscient Parity Benchmark")
    print("=" * 70)

    repo_root = pathlib.Path(__file__).resolve().parents[2]
    kernel = MasterARSIKernel()
    report = kernel.execute_master_evaluation(repo_root=repo_root)

    print(f"Argon Gauntlet Challenges: {report['argon_gauntlet_challenges_passed']} / 6 passed")
    for ch in report["challenges"]:
        status = "✅" if ch["passed"] else "❌"
        print(f"  {status} Challenge {ch['id']}: {ch['name']} -> {ch['details']}")

    output_path = pathlib.Path(__file__).resolve().parent / "arsi_master_report.json"
    output_path.write_text(json.dumps(report, indent=2))
    print(f"\n📊 Master Report written to: {output_path.name}")
    print(f"  Peak Online VRAM: {report['peak_online_vram_mib']} MiB (<= 4812.0 MiB)")
    print(f"  Zero Spoon-Feeding: {report['zero_spoon_feeding_verified']}")
    print(f"  Chezmoi Sync: {report['chezmoi_sync_clean']}")
    print(f"  MTP Throughput: {report['mtp_throughput_tok_per_sec']} tok/s")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
