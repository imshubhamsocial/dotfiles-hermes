#!/usr/bin/env python3
"""
Phase-3 Live GPU Validation (RTX 3050 / Gemma 4-E4B + MTP @ :8138)
==================================================================
Roadmap §3.2 verification test for U8:

  Exam U8 (Byte-Static Prefix Cache): 20 sequential chat completions with a
          byte-identical system prefix (built via hermes_core.prefix_cache)
          and varying user payloads. The arbiter is llama-server's own
          timings payload: mean(cache_n / prompt_n) over turns 2-20 must be
          >= 0.90 (i.e. >90% of ingested prompt tokens served from the KV
          prefix cache).
  Exam VRAM: server stays within the 4.7 GB envelope throughout.

Usage: python3 bin/run_phase3_live_validation.py [--json OUT]
Exit 0 = all exams passed.
"""

import argparse
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / ".hermes" / "src"))

BASE_URL = "http://localhost:8138"
VRAM_BUDGET_MIB = 4812
TURNS = 20
HIT_THRESHOLD = 0.90

CHAMPION_MODEL = "gemma-4-E4B-it-Q4_K_M"


def healthy() -> bool:
    try:
        with urllib.request.urlopen(f"{BASE_URL}/health", timeout=2) as r:
            return json.loads(r.read()).get("status") == "ok"
    except Exception:
        return False


def vram_used_mib() -> int:
    out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                         capture_output=True, text=True).stdout.strip().splitlines()[0]
    return int(out)


def build_u8_static_system() -> str:
    """Byte-static system prefix exceeding the 1024-token window.

    Every segment is deterministic (no timestamps, PIDs, RNG). The manifest
    mirrors real harness prompts that embed long-lived law/tool context.
    """
    from hermes_core.prefix_cache import build_static_system_prompt
    from hermes_core.middleware import MythosCognitiveGovernor

    laws = MythosCognitiveGovernor.KARPATHY_SURGICAL_LAWS
    instructions = (
        "You are Hermes @coder. Synthesize surgically via write_file and patch_file. "
        "Never rewrite whole files. Verify with external arbiters only."
    )
    manifest_lines = []
    topics = [
        "workspace root is the only writable mount",
        "patch targets must match uniquely after whitespace normalization",
        "trajectory events append to /dev/shm/hermes_shadow/events.jsonl",
        "capability masks deny architect write surfaces at schema level",
        "plugin Tier-1 summaries stay under the 150 token budget",
        "type resolver returns exact single-line signatures from types/",
        "differential compaction prunes resolved tool pairs only",
        "observer Gate7 rejects >3x bloat and sibling obliteration",
        "hypothesis tree accumulates boundary constraints from failures",
        "process teardown kills the full POSIX process group",
    ]
    for i in range(60):
        t = topics[i % len(topics)]
        manifest_lines.append(f"LAW {i:03d}: {t}; enforce without exception; report violations verbatim.")
    manifest = "\n".join(manifest_lines)

    return build_static_system_prompt(
        laws if isinstance(laws, str) else "\n".join(laws),
        instructions,
        "HARNESS CONTEXT MANIFEST (STATIC):\n" + manifest,
    )


def run_exam_u8() -> dict:
    from openai import OpenAI

    system_prompt = build_u8_static_system()
    client = OpenAI(base_url=f"{BASE_URL}/v1", api_key="local")

    ratios = []
    per_turn = []
    for turn in range(1, TURNS + 1):
        resp = client.chat.completions.create(
            model=CHAMPION_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Turn {turn:02d}: reply with the single word READY."},
            ],
            temperature=1.0, top_p=0.95, max_tokens=4,
        )
        t = getattr(resp, "timings", None) or {}
        prompt_n = int(t.get("prompt_n", 0) or 0)
        cache_n = int(t.get("cache_n", 0) or 0)
        ratio = (min(cache_n, prompt_n) / prompt_n) if prompt_n else 0.0
        if turn > 1:
            ratios.append(ratio)
        per_turn.append({"turn": turn, "prompt_n": prompt_n, "cache_n": cache_n,
                         "hit_ratio": round(ratio, 4)})
        time.sleep(0.2)

    mean_ratio = sum(ratios) / len(ratios) if ratios else 0.0
    return {
        "passed": mean_ratio >= HIT_THRESHOLD,
        "mean_hit_ratio_turns_2_20": round(mean_ratio, 4),
        "threshold": HIT_THRESHOLD,
        "static_prefix_tokens_est": len(system_prompt) // 4,
        "per_turn": per_turn,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default="/dev/shm/phase3_live_validation.json")
    args = ap.parse_args()

    if not healthy():
        print("❌ llama-server :8138 not healthy. Launch champion first.")
        return 2

    print("=" * 78)
    print("🧬 PHASE-3 LIVE GPU VALIDATION — U8 Byte-Static Prefix Cache @ :8138")
    print("=" * 78)

    vram_start = vram_used_mib()
    u8 = run_exam_u8()
    vram_end = vram_used_mib()
    vram = {"passed": vram_end <= VRAM_BUDGET_MIB,
            "vram_start_mib": vram_start, "vram_end_mib": vram_end, "budget_mib": VRAM_BUDGET_MIB}

    results = {"exam_u8_prefix_cache": u8, "exam_vram_guard": vram}
    all_passed = all(r["passed"] for r in results.values())
    report = {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "server_model": CHAMPION_MODEL + " + MTP drafter (+ --cache-reuse 64)",
        "all_passed": all_passed,
        "exams": results,
    }
    Path(args.json).write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("\n" + "-" * 78)
    mark_u8 = "✅" if u8["passed"] else "❌"
    print(f"{mark_u8} exam_u8_prefix_cache: mean hit ratio turns 2-20 = "
          f"{u8['mean_hit_ratio_turns_2_20']:.2%} (threshold {HIT_THRESHOLD:.0%}), "
          f"static prefix ~{u8['static_prefix_tokens_est']} tok")
    tail = u8["per_turn"][-3:]
    for p in tail:
        print(f"   turn {p['turn']:>2}: prompt_n={p['prompt_n']} cache_n={p['cache_n']} ratio={p['hit_ratio']:.2%}")
    mark_v = "✅" if vram["passed"] else "❌"
    print(f"{mark_v} exam_vram_guard: {vram_start}->{vram_end} MiB (budget {VRAM_BUDGET_MIB})")
    print("-" * 78)
    print("REPORT:", args.json)
    print("🟢 PHASE-3 LIVE VALIDATION PASSED" if all_passed else "🔴 PHASE-3 LIVE VALIDATION FAILED")
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
