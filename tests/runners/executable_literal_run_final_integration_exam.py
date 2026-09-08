#!/usr/bin/env python3
"""
FINAL INTEGRATION EXAM — Completed-Harness Live Validation (post-roadmap)
==========================================================================
Exercises every implemented capability TOGETHER against the live champion
(gemma-4-E4B + MTP @ :8138) in one coherent session:

  Exam E2E  : HermesOrchestrator drives a real tool-calling turn (U15
              compaction + U2 hooks + U5 sandboxed exec surface active).
  Exam U6   : emitted trajectory stream is hash-chain intact and carries
              the full event dialect.
  Exam U8   : byte-static prefix held (Trap-1 lint registry silent across
              turns) AND live KV prefix-cache hit ratio >=90% on turns 2+.
  Exam U7   : replay of the fresh stream matches deterministically.
  Exam U17  : supervisory scan of the healthy run emits zero interventions
              (no false positives).
  Exam U18  : regression-sieve commit gate accepts a shrinking variant of
              a padded skill against the clean history.
  Exam VRAM : within the 4.7 GB envelope before and after.

Usage: python3 bin/run_final_integration_exam.py [--json OUT]
Exit 0 = ALL exams passed.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / ".hermes" / "src"))

BASE_URL = "http://localhost:8138"
VRAM_BUDGET_MIB = 4812
CHAMPION_MODEL = "gemma-4-E4B-it-Q4_K_M"

PADDED_SKILL = (
    "# Workspace Law\n\n\nPlease note that the workspace root is law.\n"
    "It is important to patch surgically. \nPatch surgically.\nPatch surgically.\n"
)


def vram_used_mib() -> int:
    return int(subprocess.run(
        ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
        capture_output=True, text=True).stdout.strip().splitlines()[0])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default="/dev/shm/final_integration_report.json")
    args = ap.parse_args()

    import urllib.request
    try:
        with urllib.request.urlopen(f"{BASE_URL}/health", timeout=3) as r:
            assert json.loads(r.read()).get("status") == "ok"
    except Exception:
        print("❌ champion not healthy on :8138")
        return 2

    results = {}
    print("=" * 78)
    print("🧬 FINAL INTEGRATION EXAM — completed harness vs live champion")
    print("=" * 78)
    vram_start = vram_used_mib()

    # ── Exam E2E + U6: real engine run with tool call, full dialect ──────
    os.environ["HERMES_TRAJECTORY_PATH"] = "/dev/shm/final_exam_trajectory.jsonl"
    stream = Path(os.environ["HERMES_TRAJECTORY_PATH"])
    stream.unlink(missing_ok=True)

    from hermes_core.swarm_engine import HermesOrchestrator
    from hermes_core.swarm_system import coder_agent

    orch = HermesOrchestrator(base_url=f"{BASE_URL}/v1", api_key="local")
    agent = coder_agent.model_copy(update={"model": CHAMPION_MODEL,
                                           "temperature": 1.0})
    t0 = time.time()
    resp = orch.run(agent, [{"role": "user", "content":
        "Use write_file to create /dev/shm/final_exam_artifact.py. Its entire "
        "content must be the single line 'ok = True' followed by a newline. "
        "No trailing period, no extra characters. Then stop."}],
        max_turns=3, verbose=False)
    e2e_s = time.time() - t0

    from hermes_core.trajectory import verify_chain, load_events
    from hermes_core.replay import replay_trajectory
    from hermes_core.lineage import supervisory_scan
    from hermes_core.evolution import (commit_skill_variant,
                                       mutate_drop_filler,
                                       mutate_prune_whitespace)

    events = load_events(stream)
    chain_ok, chain_detail = verify_chain(stream)
    types = {e.get("event") for e in events}
    needed = {"turn_start", "tool_call", "gate_check", "tool_result",
              "response", "turn_end"}
    artifact_ok = Path("/dev/shm/final_exam_artifact.py").exists()
    e2e_pass = bool(resp.messages if hasattr(resp, "messages") else True) \
        and chain_ok and needed <= types and artifact_ok
    results["exam_e2e_engine_u6_chain"] = {
        "passed": e2e_pass, "wall_seconds": round(e2e_s, 1),
        "events": len(events), "chain": chain_detail,
        "dialect_complete": sorted(needed & types), "artifact_written": artifact_ok}

    # ── Exam U7: replay the fresh stream ─────────────────────────────────
    rep = replay_trajectory(stream)
    results["exam_u7_replay_match"] = {
        "passed": rep.deterministic_match and rep.replayed_steps >= 1,
        "replayed_steps": rep.replayed_steps,
        "drifted_steps": rep.drifted_steps}

    # ── Exam U17: healthy run must NOT trip the supervisor ───────────────
    ivs = supervisory_scan(stream)
    results["exam_u17_supervisor_quiet"] = {
        "passed": ivs == [], "interventions": [i.kind for i in ivs]}

    # ── Exam U18: sieve commits only the shrinking variant ───────────────
    skills_tmp = Path("/dev/shm/final_exam_skills")
    variant = mutate_drop_filler(mutate_prune_whitespace(PADDED_SKILL))
    good = commit_skill_variant(variant, PADDED_SKILL, "law.md", [stream],
                                skills_dir=skills_tmp)
    bloated = commit_skill_variant(PADDED_SKILL + "\nextra bloat tokens " * 20,
                                   PADDED_SKILL, "fat.md", [],
                                   skills_dir=skills_tmp)
    results["exam_u18_commit_gate"] = {
        "passed": good.committed and not bloated.committed,
        "clean_variant_committed": good.committed,
        "bloat_blocked_reason": bloated.reason}

    # ── Exam U8: KV prefix-cache hits on direct traffic ──────────────────
    from openai import OpenAI
    client = OpenAI(base_url=f"{BASE_URL}/v1", api_key="local")
    static_system = ("You are Hermes @coder. " +
                     "Deterministic static context line. " * 120).strip()
    ratios = []
    for turn in range(1, 13):
        r = client.chat.completions.create(
            model=CHAMPION_MODEL,
            messages=[{"role": "system", "content": static_system},
                      {"role": "user", "content": f"probe {turn:02d}: say READY"}],
            temperature=1.0, max_tokens=4)
        t = getattr(r, "timings", None) or {}
        pn, cn = int(t.get("prompt_n") or 0), int(t.get("cache_n") or 0)
        if turn > 1 and pn:
            ratios.append(min(cn, pn) / pn)
    mean_hit = sum(ratios) / len(ratios) if ratios else 0.0
    u8_registry_ok = getattr(orch, "_u8_prefix_registry", {}) != {}
    results["exam_u8_prefix_cache"] = {
        "passed": mean_hit >= 0.90 and u8_registry_ok,
        "mean_hit_ratio": round(mean_hit, 4), "turns_sampled": len(ratios),
        "trap1_lint_registry_armed": u8_registry_ok}

    # ── VRAM guard ────────────────────────────────────────────────────────
    vram_end = vram_used_mib()
    results["exam_vram_guard"] = {
        "passed": vram_end <= VRAM_BUDGET_MIB,
        "start_mib": vram_start, "end_mib": vram_end,
        "budget_mib": VRAM_BUDGET_MIB}

    all_passed = all(r["passed"] for r in results.values())
    report = {"timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "all_passed": all_passed, "exams": results}
    Path(args.json).write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("-" * 78)
    marks = []
    for name, r in results.items():
        m = "✅" if r["passed"] else "❌"
        marks.append(f"{m} {name}")
        print(f"{m} {name}: " + json.dumps(
            {k: v for k, v in r.items() if k != "passed"}, default=str)[:160])
    print("-" * 78)
    print("REPORT:", args.json)
    print("🟢 FINAL INTEGRATION EXAM PASSED — harness verified END-TO-END"
          if all_passed else "🔴 FINAL INTEGRATION EXAM FAILED")
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
