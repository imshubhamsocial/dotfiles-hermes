"""
Contract Tests: Pillar III — EvoHarness-RL Cycle & Model Evolution
===================================================================
Validates:
  1. Base task success signal calculation (+1.0 for verified sessions).
  2. Test passage bonus (+0.5 when test logs contain pass verification).
  3. Spec-first bonus (+0.3 when plan/spec formulated before mutation).
  4. Token waste penalty when turns exceed budget.
  5. Hardcoded non-portable path penalty (-0.5).
  6. VRAM ceiling violation penalty (-1.0).
  7. Batch trajectory scoring with reward distribution metrics.
  8. SFT dataset curation filters top percentile trajectories into instruction dataset.
  9. LoRA training script generation with hardware assertions.
 10. LoRA offline training dry-run validates quantization and VRAM budget.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
import pytest

from plugins.reward_scorer import (
    ConstitutionalRewardScorer,
    SFTDataCurator,
    LoRATrainingCoordinator,
)


def test_reward_scorer_base_success():
    traj = {"session_id": "s1", "verified": True, "turns_count": 2, "summary": "Task complete"}
    res = ConstitutionalRewardScorer.score_trajectory(traj)
    assert res["signals"]["task_completion"] == 1.0
    assert res["total_reward"] >= 1.0
    assert res["passed_threshold"] is True


def test_reward_scorer_test_passage_bonus():
    traj = {
        "session_id": "s2",
        "verified": True,
        "turns_count": 3,
        "summary": "118 passed in 19.81s. All exam checks passed.",
    }
    res = ConstitutionalRewardScorer.score_trajectory(traj)
    assert res["signals"]["test_passage_bonus"] == 0.5
    assert res["total_reward"] >= 1.5


def test_reward_scorer_spec_first_bonus():
    traj = {
        "session_id": "s3",
        "verified": True,
        "turns_count": 4,
        "summary": "Generated engineering spec and plan.json before implementing code.",
    }
    res = ConstitutionalRewardScorer.score_trajectory(traj)
    assert res["signals"]["spec_first_bonus"] == 0.3
    assert res["total_reward"] >= 1.3


def test_reward_scorer_token_waste_penalty():
    traj = {
        "session_id": "s4",
        "verified": True,
        "turns_count": 25,  # 10 turns over 15 budget
        "summary": "Long meandering session",
    }
    res = ConstitutionalRewardScorer.score_trajectory(traj)
    assert res["signals"]["token_waste_penalty"] < 0.0


def test_reward_scorer_hardcoded_path_penalty():
    traj = {
        "session_id": "s5",
        "verified": True,
        "turns_count": 2,
        "turns": [{"cmd": "cat /var/home/someuser/documents/secret.txt"}],
    }
    res = ConstitutionalRewardScorer.score_trajectory(traj)
    assert res["signals"]["hardcoded_path_penalty"] == -0.5


def test_reward_scorer_vram_exceeded_penalty():
    traj = {
        "session_id": "s6",
        "verified": True,
        "vram_exceeded": True,
    }
    res = ConstitutionalRewardScorer.score_trajectory(traj)
    assert res["signals"]["vram_ceiling_penalty"] == -1.0


def test_score_all_samples_batch(tmp_path):
    in_file = tmp_path / "samples.jsonl"
    out_file = tmp_path / "scored.jsonl"

    samples = [
        {"session_id": "batch_1", "verified": True, "turns_count": 3, "summary": "All exam checks passed."},
        {"session_id": "batch_2", "verified": False, "turns_count": 1, "summary": "Incomplete"},
    ]
    with open(in_file, "w") as f:
        for s in samples:
            f.write(json.dumps(s) + "\n")

    res = ConstitutionalRewardScorer.score_all_samples(buffer_file=in_file, output_file=out_file)
    assert res["total_scored"] == 2
    assert out_file.exists()


def test_sft_data_curator_selection(tmp_path):
    scored_file = tmp_path / "scored.jsonl"
    sft_file = tmp_path / "sft_data.jsonl"

    scored_entries = [
        {"session_id": f"s_{i}", "title": f"Task {i}", "reward_evaluation": {"total_reward": 1.0 + (i * 0.2)}}
        for i in range(10)
    ]
    with open(scored_file, "w") as f:
        for e in scored_entries:
            f.write(json.dumps(e) + "\n")

    res = SFTDataCurator.curate(scored_file=scored_file, sft_output=sft_file, percentile=0.3)
    assert res["curated_count"] == 3
    assert sft_file.exists()


def test_lora_training_script_generation(tmp_path):
    script = tmp_path / "train.py"
    res = LoRATrainingCoordinator.generate_training_script(output_script_path=script)
    assert res.exists()
    assert "QLoRA" in res.read_text()
    assert "4,500 MiB" in res.read_text()


def test_lora_dry_run_execution(tmp_path):
    script = tmp_path / "train.py"
    LoRATrainingCoordinator.generate_training_script(output_script_path=script)

    import subprocess
    ret = subprocess.run(["python3", str(script), "--dry-run"], capture_output=True, text=True)
    assert ret.returncode == 0
    assert "Dry-run completed successfully" in ret.stdout


def test_sft_data_curator_enrichment(tmp_path):
    scored_file = tmp_path / "scored_enrich.jsonl"
    sft_file = tmp_path / "sft_enrich.jsonl"
    sample = {
        "session_id": "test_sid",
        "title": "Fallback Title",
        "summary": "Completed verified task",
        "turns": [
            {"user": "Do this specific task"},
            {"assistant": "Here is the completed task solution"}
        ],
        "reward_evaluation": {"total_reward": 1.8}
    }
    with open(scored_file, "w") as f:
        f.write(json.dumps(sample) + "\n")

    res = SFTDataCurator.curate(scored_file=scored_file, sft_output=sft_file, percentile=1.0)
    assert res["curated_count"] == 1
    with open(sft_file, "r") as f:
        data = json.loads(f.readline())
    assert data["instruction"] == "Do this specific task"
    assert data["output"] == "Here is the completed task solution"
    assert data["reward"] == 1.8


def test_frognano_learnability_frontier_filter():
    tasks = [
        {"session_id": "trivial", "reward": 0.95},
        {"session_id": "impossible", "reward": 0.1},
        {"session_id": "frontier_1", "reward": 0.5},
        {"session_id": "frontier_2", "reward": 0.65},
    ]
    calibrated = ConstitutionalRewardScorer.calibrate_difficulty(tasks, score_range=(0.3, 0.7))
    assert len(calibrated) == 2
    ids = [t["session_id"] for t in calibrated]
    assert "frontier_1" in ids
    assert "frontier_2" in ids
    assert "trivial" not in ids
    assert "impossible" not in ids


def test_sft_curator_frontier_only_mode(tmp_path):
    scored_file = tmp_path / "scored.jsonl"
    out_file = tmp_path / "sft_frontier.jsonl"

    records = [
        {"session_id": "r1", "reward": 0.95, "title": "Easy task", "summary": "Done immediately"},
        {"session_id": "r2", "reward": 0.55, "title": "Frontier task", "summary": "Challenging task solved"},
        {"session_id": "r3", "reward": 0.15, "title": "Failed task", "summary": "Failed task"},
    ]
    scored_file.write_text("\n".join(json.dumps(r) for r in records), encoding="utf-8")

    res = SFTDataCurator.curate(scored_file=scored_file, output_file=out_file, percentile=1.0, frontier_only=True)
    assert res["curated_count"] == 1
    content = out_file.read_text(encoding="utf-8")
    assert "Frontier task" in content
    assert "Easy task" not in content
