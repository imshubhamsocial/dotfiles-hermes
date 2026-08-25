#!/usr/bin/env python3
"""
Phase-4 Contract Spike: Trajectory Lineage & AlphaEvolve Substrate (U6)
=======================================================================
Versioned contract test for Phase 4 (roadmap §3.4-B).

  - U6 Append-Only Trajectory Event Stream: every turn / tool payload /
    gate verdict / test result lands as an immutable hash-chained JSONL
    record. Active stream lives on RAMDisk (Btrfs zero-wear law);
    milestone flush copies once with chattr +C.
  - Chain verification detects ANY mutation, deletion or reordering
    after the fact (tamper evidence), plus seq continuity gaps.

100% offline & deterministic.
Run: pytest tests/harness_contracts/test_lineage_rollback_and_alphaevolve.py -q
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from hermes_core import trajectory as traj


@pytest.fixture()
def stream(tmp_path, monkeypatch):
    p = tmp_path / "trajectory.jsonl"
    monkeypatch.setenv("HERMES_TRAJECTORY_PATH", str(p))
    return p


# ─── U6: Schema & sealing ────────────────────────────────────────────────────

def test_u6_event_schema_core_fields(stream):
    rec = traj.TrajectoryRecorder(session_id="s1")
    ev = rec.record_turn(turn=12, role="coder", prompt_tokens=1420)
    for key in ("seq", "ts", "session", "event", "turn", "role",
                "prompt_tokens", "prev", "hash"):
        assert key in ev, f"missing core field {key}"
    assert len(ev["hash"]) == 64 and ev["seq"] == 0


def test_u6_spec_example_fields_roundtrip(stream):
    rec = traj.TrajectoryRecorder(session_id="s1")
    rec.record_turn(turn=12, role="coder", prompt_tokens=1420)
    rec.record_gate(turn=12, tool="patch", gate_status="PASS")
    ev = rec.record_test(turn=12, test_passed=True, command="pytest -q")
    assert ev["command"] == "pytest -q"
    events = traj.load_events(stream)
    by_type = {e["event"]: e for e in events}
    assert by_type["turn_start"]["prompt_tokens"] == 1420
    assert by_type["gate_check"]["gate_status"] == "PASS"
    assert by_type["test_result"]["test_passed"] is True


def test_u6_unknown_event_type_rejected(stream):
    rec = traj.TrajectoryRecorder(session_id="s1")
    with pytest.raises(ValueError):
        rec.append(event="not_a_real_event", turn=1)


# ─── U6: Append-only chain semantics ─────────────────────────────────────────

def test_u6_chain_continuous_across_recorders(stream):
    r1 = traj.TrajectoryRecorder(session_id="s1")
    r2 = traj.TrajectoryRecorder(session_id="s2")
    r1.record_turn(turn=1, role="architect")
    r2.record_turn(turn=2, role="coder")
    r1.record_test(turn=2, test_passed=True)
    ok, _ = traj.verify_chain(stream)
    assert ok
    seqs = [e["seq"] for e in traj.load_events(stream)]
    assert seqs == sorted(seqs) == list(range(len(seqs)))


def test_u6_tamper_detection_hash_mutation(stream):
    rec = traj.TrajectoryRecorder(session_id="s1")
    for t in range(3):
        rec.record_turn(turn=t, role="coder", prompt_tokens=t * 10)
    raw = stream.read_text().splitlines()
    victim = json.loads(raw[1])
    victim["role"] = "TAMPERED"
    raw[1] = json.dumps(victim, sort_keys=True, separators=(",", ":"))
    stream.write_text("\n".join(raw) + "\n")
    ok, detail = traj.verify_chain(stream)
    assert not ok and "hash mismatch" in detail


def test_u6_seq_gap_detection(stream):
    rec = traj.TrajectoryRecorder(session_id="s1")
    for t in range(3):
        rec.record_turn(turn=t, role="coder")
    lines = stream.read_text().splitlines()
    del lines[1]  # silent deletion attempt
    stream.write_text("\n".join(lines) + "\n")
    ok, detail = traj.verify_chain(stream)
    assert not ok and "seq discontinuity" in detail


# ─── U6: Storage law (RAMDisk-active, flush-on-milestone) ────────────────────

def test_u6_default_path_is_ramdisk_not_repo(stream, monkeypatch):
    monkeypatch.delenv("HERMES_TRAJECTORY_PATH", raising=False)
    assert str(traj.active_path()).startswith("/dev/shm/")
    rec = traj.TrajectoryRecorder(session_id="sX")
    rec.record_turn(turn=0, role="tester")
    assert not (ROOT / traj.CANONICAL_RELATIVE).exists(), \
        "active appends must never touch repo storage"


def test_u6_milestone_flush_merges_without_loss(stream, tmp_path):
    target = tmp_path / "milestone" / "trajectory.jsonl"
    r = traj.TrajectoryRecorder(session_id="m1")
    r.record_turn(turn=1, role="coder")
    first = traj.flush_to_milestone_disk(target=target)
    assert str(first["target"]) == str(target)
    assert first["chain_valid_after_merge"] is True
    size_after_first = target.stat().st_size
    r.record_turn(turn=2, role="coder")  # post-flush event lands in new stream
    second = traj.flush_to_milestone_disk(target=target)
    assert second["events_merged"] == 1 and second["chain_valid_after_merge"] is True
    assert target.stat().st_size > size_after_first
    ok, _ = traj.verify_chain(target)
    assert ok, "merged milestone file must remain a valid chain"


def test_u6_fifty_turn_exam_all_events_in_ram(stream):
    rec = traj.TrajectoryRecorder(session_id="bench")
    t0 = time.perf_counter()
    for t in range(50):
        rec.record_turn(turn=t, role="coder", prompt_tokens=1420 + t)
        if t % 5 == 0:
            rec.record_gate(turn=t, tool="patch", gate_status="PASS")
        if t % 10 == 0:
            rec.record_test(turn=t, test_passed=True, command="pytest -q")
    dur = time.perf_counter() - t0
    ok, detail = traj.verify_chain(stream)
    n = len(traj.load_events(stream))
    assert ok and n == 65 and dur < 5.0
    assert stream.stat().st_size < 1024 * 1024  # Trap-1: <1 MB per 50 turns


# ─── U7: Deterministic Trajectory Replay & Distillation ──────────────────────

import json as _json

from hermes_core.replay import TrajectoryTamperError, replay_trajectory


GOOD_ARGS = _json.dumps({"filepath": "m.py", "content": "x = 1\n"})
BAD_ARGS = _json.dumps({"filepath": "b.py", "content": "def broken(:\n"})


def _record_step(rec, turn, tool, args_head, gate, result_ok, role="coder"):
    rec.record_tool_call(turn=turn, role=role, tool=tool, args_head=args_head)
    rec.record_gate(turn=turn, tool=tool, gate_status=gate)
    return rec.record_tool_result(turn=turn, tool=tool,
                                  result_ok=result_ok,
                                  result_head="ok" if result_ok else "Error: x")


def test_u7_clean_replay_is_deterministic_match(stream):
    rec = traj.TrajectoryRecorder(session_id="u7a")
    for t in range(5):
        _record_step(rec, t, "write_file", GOOD_ARGS, "PASS", True)
    report = replay_trajectory(stream)
    assert report.deterministic_match is True
    assert report.replayed_steps == 5 and report.drifted_steps == 0
    assert all(s.drift_kind == "" for s in report.steps)


def test_u7_linter_drift_detected_when_new_rules_reject_past_success(stream):
    rec = traj.TrajectoryRecorder(session_id="u7b")
    # Past-lax-linter world: syntax-broken payload recorded as PASS/success.
    _record_step(rec, 1, "write_file", BAD_ARGS, "PASS", True)
    report = replay_trajectory(stream)
    assert report.deterministic_match is False
    step = report.steps[0]
    assert "LINTER_DRIFT" in step.drift_kind
    assert "CONTRADICTION" in step.drift_kind
    assert step.replayed_gate == "REJECT" and step.recorded_gate == "PASS"


def test_u7_contradiction_without_linter_drift_flagged(stream):
    rec = traj.TrajectoryRecorder(session_id="u7c")
    # Rules already rejected back then, but success was recorded anyway.
    _record_step(rec, 2, "write_file", BAD_ARGS, "REJECT", True)
    report = replay_trajectory(stream)
    step = report.steps[0]
    assert step.drift is True and step.drift_kind == "CONTRADICTION"
    assert step.recorded_gate == step.replayed_gate == "REJECT"


def test_u7_replay_refuses_tampered_stream(stream):
    rec = traj.TrajectoryRecorder(session_id="u7d")
    _record_step(rec, 1, "write_file", GOOD_ARGS, "PASS", True)
    raw = stream.read_text().splitlines()
    victim = _json.loads(raw[0]); victim["tool"] = "TAMPERED"
    raw[0] = _json.dumps(victim, sort_keys=True, separators=(",", ":"))
    stream.write_text("\n".join(raw) + "\n")
    with pytest.raises(TrajectoryTamperError):
        replay_trajectory(stream)


def test_u7_unresolved_call_counts_as_skipped_not_drift(stream):
    rec = traj.TrajectoryRecorder(session_id="u7e")
    rec.record_tool_call(turn=9, role="coder", tool="read_file",
                         args_head=_json.dumps({"filepath": "a.py"}))
    report = replay_trajectory(stream)
    assert report.replayed_steps == 0 and report.skipped_events == 1
    assert report.deterministic_match is True  # vacuous pass, honestly reported


def test_u7_max_steps_cap_and_report_schema(stream):
    rec = traj.TrajectoryRecorder(session_id="u7f")
    for t in range(6):
        _record_step(rec, t, "write_file", GOOD_ARGS, "PASS", True)
    report = replay_trajectory(stream, max_steps=3)
    s = report.summary()
    assert s["replayed_steps"] == 3
    for key in ("source", "total_events", "replayed_steps", "clean_steps",
                "drifted_steps", "deterministic_match", "skipped_events"):
        assert key in s


# ─── U17: AVO Lineage Search & Supervisory Recovery ──────────────────────────

from hermes_core.lineage import (
    FIXATION_LIMIT,
    STALL_WINDOW,
    Intervention,
    LineageNode,
    build_lineage_tree,
    load_tree,
    save_tree,
    select_branch_point,
    supervisory_scan,
)


def _u17_step(rec, turn, tool, filepath, ok):
    args = _json.dumps({"filepath": filepath, "content": "v = 1\n"})
    rec.record_tool_call(turn=turn, role="coder", tool=tool, args_head=args)
    rec.record_gate(turn=turn, tool=tool, gate_status="PASS" if ok else "REJECT")
    rec.record_tool_result(turn=turn, tool=tool, result_ok=ok,
                           result_head="ok" if ok else "Error: failed")


def test_u17_lineage_builds_from_trajectory(stream):
    rec = traj.TrajectoryRecorder(session_id="u17a")
    _u17_step(rec, 0, "write_file", "a.py", True)
    _u17_step(rec, 1, "patch_file", "a.py", False)
    _u17_step(rec, 2, "write_file", "b.py", True)
    nodes = build_lineage_tree(traj.load_events(stream))
    assert len(nodes) == 3
    assert [n.parent_id for n in nodes] == [None, 0, 1]
    assert [n.fitness for n in nodes] == [1.0, 0.0, 1.0]
    assert nodes[0].children == [1]
    assert nodes[1].filepath == "a.py"


def test_u17_branch_point_prefers_high_fitness_ancestor(stream):
    rec = traj.TrajectoryRecorder(session_id="u17b")
    _u17_step(rec, 0, "write_file", "good.py", True)
    for t in range(1, 4):
        _u17_step(rec, t, "patch_file", "broken.py", False)
    nodes = build_lineage_tree(traj.load_events(stream))
    bp = select_branch_point(nodes)
    assert bp is not None and bp.filepath == "good.py" and bp.node_id == 0


def test_u17_branch_point_excludes_banned_subtrees(stream):
    rec = traj.TrajectoryRecorder(session_id="u17c")
    _u17_step(rec, 0, "write_file", "root.py", True)     # node0 good
    _u17_step(rec, 1, "write_file", "mid.py", True)      # node1 good (descendant of 0)
    _u17_step(rec, 2, "write_file", "bad.py", False)     # node2 fail
    nodes = build_lineage_tree(traj.load_events(stream))
    assert select_branch_point(nodes).node_id == 1
    bp = select_branch_point(nodes, exclude_node_ids={1})
    assert bp.node_id == 0, "banning node1 must fall back to its ancestor"


def test_u17_tree_persistence_roundtrip(tmp_path, stream):
    rec = traj.TrajectoryRecorder(session_id="u17d")
    _u17_step(rec, 0, "write_file", "x.py", True)
    nodes = build_lineage_tree(traj.load_events(stream))
    path = save_tree(nodes, path=tmp_path / "lineage_tree.json")
    rt = load_tree(path)
    assert [(n.node_id, n.tool, n.result_ok) for n in rt] == \
           [(n.node_id, n.tool, n.result_ok) for n in nodes]


def test_u17_stall_window_triggers_ancestor_rollback(stream):
    rec = traj.TrajectoryRecorder(session_id="u17e")
    _u17_step(rec, 0, "write_file", "good.py", True)
    for t in range(1, 1 + STALL_WINDOW):  # full window of zero progress
        _u17_step(rec, t, "patch_file", f"f{t}.py", False)
    ivs = supervisory_scan(stream)
    rollbacks = [i for i in ivs if i.kind == "ROLLBACK_TO_ANCESTOR"]
    assert rollbacks, "stall must trigger ancestor rollback"
    assert rollbacks[0].branch_to_node is not None


def test_u17_same_file_fixation_switches_operator(stream):
    rec = traj.TrajectoryRecorder(session_id="u17f")
    _u17_step(rec, 0, "write_file", "good.py", True)
    for t in range(1, 1 + FIXATION_LIMIT):  # same broken file repeatedly
        _u17_step(rec, t, "patch_file", "stubborn.py", False)
    ivs = supervisory_scan(stream)
    switches = [i for i in ivs if i.kind == "SWITCH_OPERATOR"]
    assert switches and "stubborn.py" in switches[0].reason
    assert "local-minimum fixation" in switches[0].reason


def test_u17_healthy_stream_emits_no_interventions(stream):
    rec = traj.TrajectoryRecorder(session_id="u17g")
    outcomes = [True, False, True, True, False, True, True, True]
    for t, ok in enumerate(outcomes):
        _u17_step(rec, t, "write_file", f"h{t}.py", ok)
    assert supervisory_scan(stream) == []


def test_u17_non_mutating_stream_is_clean(stream):
    rec = traj.TrajectoryRecorder(session_id="u17h")
    for t in range(8):
        _record_step(rec, t, "read_file",
                     _json.dumps({"filepath": "r.py"}), "PASS", True)
    assert supervisory_scan(stream) == []
    assert build_lineage_tree(traj.load_events(stream)) == []


# ─── U18: Self-Evolution & AlphaEvolve Numerical Sieve ───────────────────────

from fractions import Fraction

from hermes_core.evolution import (
    commit_skill_variant,
    evolve_one_generation,
    gepa_loss,
    mutate_drop_filler,
    mutate_prune_whitespace,
    pareto_frontier,
    run_numerical_sieve,
    verify_rational_exact,
)


PADDED_SKILL = (
    "# Skill\n\n\nPlease note that the workspace law is law.\n"
    "It is important to patch surgically. \nPatch surgically.\nPatch surgically.\n"
)


def test_u18_mutations_shrink_without_losing_markers():
    pruned = mutate_prune_whitespace(PADDED_SKILL)
    assert "\n\n\n" not in pruned and len(pruned) < len(PADDED_SKILL)
    unfilled = mutate_drop_filler(PADDED_SKILL)
    assert "Please note that" not in unfilled
    assert "workspace law is law." in unfilled, "semantic markers must survive"
    offspring = evolve_one_generation(PADDED_SKILL)
    assert len(offspring) >= 2 and all(len(v) <= len(PADDED_SKILL) for v in offspring)


def test_u18_pareto_frontier_drops_dominated_variants():
    base = "alpha beta gamma delta"
    tight = "alpha-beta-gamma-delta"          # same pass, fewer tokens
    bloated = base + " plus lots of extra filler commentary tokens"
    front = pareto_frontier([(base, 1.0), (tight, 1.0), (bloated, 0.5)])
    assert bloated not in front
    assert tight in front


def test_u18_gepa_loss_formula_monotonicity():
    padded = PADDED_SKILL
    pruned = mutate_prune_whitespace(mutate_drop_filler(padded))
    loss_pad = gepa_loss(padded, pass_rate=1.0)
    loss_prune = gepa_loss(pruned, pass_rate=1.0)
    assert loss_prune < loss_pad, "fewer tokens at equal pass rate must lower Loss"
    assert gepa_loss(pruned, pass_rate=0.5) > loss_prune


def test_u18_commit_gate_allows_clean_history_no_bloat(stream, tmp_path):
    rec = traj.TrajectoryRecorder(session_id="u18a")
    _record_step(rec, 0, "write_file", GOOD_ARGS, "PASS", True)
    variant = mutate_drop_filler(mutate_prune_whitespace(PADDED_SKILL))
    d = commit_skill_variant(variant, PADDED_SKILL, "law_skill.md",
                             [stream], skills_dir=tmp_path / "skills")
    assert d.committed and d.history_replay_clean
    assert (tmp_path / "skills" / "law_skill.md").read_text() == variant


def test_u18_commit_gate_blocks_on_history_drift(stream, tmp_path):
    # Stale-PASS world: today's rules reject a payload history recorded as OK.
    rec = traj.TrajectoryRecorder(session_id="u18b")
    _record_step(rec, 0, "write_file", BAD_ARGS, "PASS", True)
    d = commit_skill_variant("tight prompt", PADDED_SKILL, "s.md", [stream],
                             skills_dir=tmp_path / "skills")
    assert not d.committed
    assert "regression sieve failed" in d.reason
    assert not (tmp_path / "skills" / "s.md").exists()


def test_u18_commit_gate_blocks_token_bloat(tmp_path):
    bloated = PADDED_SKILL + "\nAdditional verbose paragraph appended to bloat the skill far beyond its original footprint."
    d = commit_skill_variant(bloated, PADDED_SKILL, "bloat.md", [],
                             skills_dir=tmp_path / "skills")
    assert not d.committed and "token bloat blocked" in d.reason
    assert not (tmp_path / "skills" / "bloat.md").exists()


def test_u18_rational_verification_rejects_ieee_drift():
    ok, _ = verify_rational_exact("3/10", Fraction(3, 10))
    assert ok
    ok, msg = verify_rational_exact("0.30000000000000004", Fraction(3, 10))
    assert not ok and "precision drift" in msg
    ok, msg = verify_rational_exact("garbage", Fraction(1, 2))
    assert not ok and "unparseable" in msg


def test_u18_numerical_sieve_end_to_end(tmp_path):
    good = tmp_path / "good_kernel.py"
    good.write_text(
        "from fractions import Fraction\n"
        "print(f'SUM={Fraction(1, 3) + Fraction(2, 3)}')\n")
    r = run_numerical_sieve(good, {"SUM": Fraction(1)})
    assert r["accepted"] and r["claims"]["SUM"]["ok"]

    drifty = tmp_path / "drifty_kernel.py"
    drifty.write_text("print('SUM=0.9999999999999999')\n")  # IEEE underflow hallucination
    r = run_numerical_sieve(drifty, {"SUM": Fraction(1)})
    assert not r["accepted"] and "precision drift" in r["claims"]["SUM"]["msg"]

    silent = tmp_path / "silent.py"
    silent.write_text("print('nothing relevant')\n")
    r = run_numerical_sieve(silent, {"SUM": Fraction(1)})
    assert not r["accepted"] and r.get("missing_claims") == ["SUM"]
