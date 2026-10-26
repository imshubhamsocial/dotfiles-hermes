"""Machine Verification Gate for Phase 25 Dream-ARSI Master Omniscient Parity."""

import json
import pathlib
import sys

# Add scenario to sys.path
scenario_dir = pathlib.Path(__file__).resolve().parent / "scenario"
sys.path.insert(0, str(scenario_dir))

from arsi_kernel import MasterARSIKernel


def test_verify_master_report():
    report_file = pathlib.Path(__file__).resolve().parent / "arsi_master_report.json"
    assert report_file.exists(), f"Missing master report: {report_file}"
    report = json.loads(report_file.read_text())

    assert report["all_14_phases_certified"] is True, "Not all 14 phases certified"
    assert report["peak_online_vram_mib"] <= 4812.0, f"VRAM ceiling breach: {report['peak_online_vram_mib']}"
    assert report["zero_spoon_feeding_verified"] is True, "Zero spoon-feeding invariant violated"
    assert report["chezmoi_sync_clean"] is True, "Chezmoi sync state is dirty"
    assert report["argon_gauntlet_challenges_passed"] == 6, f"Expected 6 challenges, got {report['argon_gauntlet_challenges_passed']}"
    assert report["active_llm_port"] == 8138, "Port 8138 LLM inactive"
    assert report["mtp_throughput_tok_per_sec"] >= 42.4, "MTP throughput below baseline"


def test_verify_epistemic_receipt():
    receipt_file = pathlib.Path("/tmp/hermes_verified_receipt.json")
    if receipt_file.exists():
        receipt = json.loads(receipt_file.read_text())
        assert receipt.get("exitstatus") == 0, f"Receipt exitstatus != 0: {receipt}"


def test_verify_live_kernel_gauntlet():
    kernel = MasterARSIKernel()
    results = kernel.run_argon_gauntlet()
    assert len(results) == 6
    assert all(r.passed for r in results)
