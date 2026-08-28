#!/usr/bin/env python3
"""
Phase-2 Live GPU Validation (RTX 3050 / Gemma 4-E4B + MTP @ :8138)
==================================================================
Closes Phase 2 by exercising the wired capabilities under REAL champion
model traffic through the HermesOrchestrator dispatch loop:

  Exam A (U3 Capability Masks): @architect runs live; the exact OpenAI
          tools schema sent over HTTP is captured by a spy wrapper and
          asserted to contain ZERO denied tools (schema-level isolation).
  Exam B (U2 Lifecycle Hooks):  @coder writes a valid module through the
          live loop (pre-hook pass -> disk -> shadow snapshot +
          trajectory event). A broken payload is then probed directly to
          prove the pre-hook rejection path emits an exact numbered slice.
  Exam C (U20 IDE Substrate):   TypeSignatureResolver resolves BufferGeometry,
          SymbolIndex indexes the Exam-B artifact, ScaffoldRegistry serves
          the WebGL boilerplate template.
  Exam D (VRAM Guard):          Server stays within the 4.7 GB envelope.

Usage: python3 bin/run_phase2_live_validation.py [--json OUT]
Exit 0 = all exams passed.
"""

import argparse
import ast
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / ".hermes" / "src"))

BASE_URL = "http://127.0.0.1:8138/v1"
VRAM_BUDGET_MIB = 4812  # 4.7 GB
CHAMPION_MODEL = "gemma-4-E4B-it-Q4_K_M"

WORKDIR = Path("/dev/shm/hermes_phase2_live")
SHADOW_DIR = Path("/dev/shm/hermes_shadow")
VALID_TARGET = WORKDIR / "hook_valid.py"

GOOGLE_SAMPLING = {"temperature": 1.0}  # top_k/top_p enforced server-side


def healthy() -> bool:
    try:
        with urllib.request.urlopen("http://localhost:8138/health", timeout=2) as r:
            return json.loads(r.read()).get("status") == "ok"
    except Exception:
        return False


def vram_used_mib() -> int:
    out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                         capture_output=True, text=True).stdout.strip().splitlines()[0]
    return int(out)


def champion(agent):
    """Clone a swarm agent onto the champion model with official Google sampling."""
    return agent.model_copy(update={
        "model": CHAMPION_MODEL,
        "temperature": GOOGLE_SAMPLING["temperature"],
    })


class SchemaSpy:
    """Captures the exact tools array sent to llama-server (deterministic arbiter)."""

    def __init__(self, orch):
        self._orig = orch.client.chat.completions.create
        self.captured_schemas = []
        orch.client.chat.completions.create = self._wrap

    def _wrap(self, **kwargs):
        self.captured_schemas.append(
            [t["function"]["name"] for t in (kwargs.get("tools") or [])]
        )
        return self._orig(**kwargs)


def run_exam_a(orch) -> dict:
    from hermes_core.swarm_system import architect_agent
    from hermes_core.capability_masks import check_tool

    spy = SchemaSpy(orch)
    agent = champion(architect_agent)
    resp = orch.run(
        agent,
        [{"role": "user", "content":
          "Blueprint only, NO tools: design a 3-milestone plan for a CLI todo app "
          "(modules, interfaces, insertion anchors). Reply with text only."}],
        max_turns=4, verbose=False,
    )

    sent = [name for schema in spy.captured_schemas for name in schema]
    denials = []
    for name in sorted(set(sent)):
        ok, _msg = check_tool("architect", name)
        if not ok:
            denials.append(name)

    leaked_writes = {"write_file", "patch_file", "execute_command", "run_test_suite",
                     "refactor_symbol"} & set(sent)

    return {
        "passed": not denials and not leaked_writes and len(resp.messages) > 0,
        "tools_sent": sorted(set(sent)),
        "denied_tools_leaked": denials,
        "write_surface_leaked": sorted(leaked_writes),
        "detail": f"{len(spy.captured_schemas)} live call(s); schema surface={sorted(set(sent))}",
    }


def run_exam_b(orch) -> dict:
    import shutil
    from hermes_core.swarm_system import coder_agent
    from hermes_core.hooks import LifecycleHookEngine

    shutil.rmtree(WORKDIR, ignore_errors=True)
    WORKDIR.mkdir(parents=True, exist_ok=True)
    events_before = _count_events()

    agent = champion(coder_agent)
    orch.run(
        agent,
        [{"role": "user", "content":
          "Use write_file ONCE to create /dev/shm/hermes_phase2_live/hook_valid.py with exactly:\n\n"
          "def validate(x: int) -> bool:\n"
          '    """Return True when x is non-negative."""\n'
          "    return x >= 0\n\n"
          "Then reply DONE. Do not create any other files."}],
        max_turns=6, verbose=False,
    )

    exists = VALID_TARGET.exists()
    syntax_ok = False
    semantics_ok = False
    if exists:
        src = VALID_TARGET.read_text(encoding="utf-8")
        try:
            ast.parse(src)
            syntax_ok = True
        except SyntaxError:
            syntax_ok = False
        try:
            mod_scope = {}
            exec(compile(src, str(VALID_TARGET), "exec"), mod_scope)
            semantics_ok = mod_scope.get("validate")(5) is True and mod_scope.get("validate")(-1) is False
        except Exception:
            semantics_ok = False

    events_after = _count_events()
    trajectory_emitted = events_after > events_before
    shadow_snapshots = list(SHADOW_DIR.glob(f"*_{VALID_TARGET.name}"))

    eng = LifecycleHookEngine()
    ok_reject, msg_reject = eng.pre_tool_call(
        "coder", "write_file",
        {"filepath": "/dev/shm/hermes_phase2_live/broken.py", "content": "def x(:\n  pass"},
    )
    rejection_slice_numbered = (not ok_reject) and ("\n1: " in f"\n{msg_reject}" or "\n2: " in f"\n{msg_reject}")

    return {
        "passed": all([exists, syntax_ok, semantics_ok, trajectory_emitted,
                       bool(shadow_snapshots), not ok_reject, rejection_slice_numbered]),
        "file_written": exists,
        "syntax_ok": syntax_ok,
        "semantics_ok": semantics_ok,
        "trajectory_event_emitted": trajectory_emitted,
        "shadow_snapshot_count": len(shadow_snapshots),
        "broken_payload_rejected": not ok_reject,
        "rejection_slice_numbered": rejection_slice_numbered,
        "rejection_head": msg_reject.splitlines()[0] if msg_reject else "",
    }


def _count_events() -> int:
    f = SHADOW_DIR / "events.jsonl"
    return len(f.read_text(encoding="utf-8").splitlines()) if f.exists() else 0


def run_exam_c() -> dict:
    from hermes_core.ide_substrate import SymbolIndex, ScaffoldRegistry, TypeSignatureResolver

    resolver = TypeSignatureResolver()
    sig = resolver.resolve("BufferGeometry")

    idx = SymbolIndex(db_path=WORKDIR / "symbols.db")
    indexed = idx.index_file(str(VALID_TARGET)) if VALID_TARGET.exists() else 0
    hits = idx.query("validate")
    idx.close()

    reg = ScaffoldRegistry()
    tpl = reg.get_template("webgl_canvas_boilerplate.html")

    sig_valid = bool(sig) and sig.startswith("class BufferGeometry") and "BufferAttribute" in sig

    return {
        "passed": all([sig_valid, indexed > 0,
                       len(hits) > 0, bool(tpl), "canvas" in (tpl or "").lower()]),
        "buffer_geometry_signature": sig,
        "symbols_indexed": indexed,
        "symbol_query_hits": len(hits),
        "scaffold_bytes": len(tpl or ""),
        "type_categories": resolver.list_categories(),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default="/dev/shm/phase2_live_validation.json")
    args = ap.parse_args()

    if not healthy():
        print("❌ llama-server :8138 not healthy. Launch champion first.")
        return 2

    from hermes_core.swarm_engine import HermesOrchestrator

    print("=" * 78)
    print("🧬 PHASE-2 LIVE GPU VALIDATION — Champion:", CHAMPION_MODEL, "+ MTP @ :8138")
    print("=" * 78)

    orch = HermesOrchestrator(base_url=BASE_URL, api_key="local")
    vram_start = vram_used_mib()
    results = {}

    print("\n[EXAM A] U3 capability masks under live @architect traffic...")
    t0 = time.time()
    results["exam_a_u3_masks"] = run_exam_a(orch)
    results["exam_a_u3_masks"]["seconds"] = round(time.time() - t0, 2)

    print("[EXAM B] U2 lifecycle hooks under live @coder traffic...")
    t0 = time.time()
    results["exam_b_u2_hooks"] = run_exam_b(orch)
    results["exam_b_u2_hooks"]["seconds"] = round(time.time() - t0, 2)

    print("[EXAM C] U20 IDE substrate resolution + indexing...")
    results["exam_c_u20_substrate"] = run_exam_c()

    vram_end = vram_used_mib()
    results["exam_d_vram_guard"] = {
        "passed": vram_end <= VRAM_BUDGET_MIB,
        "vram_start_mib": vram_start,
        "vram_end_mib": vram_end,
        "budget_mib": VRAM_BUDGET_MIB,
    }

    all_passed = all(r["passed"] for r in results.values())
    report = {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "server_model": CHAMPION_MODEL + " + MTP drafter",
        "all_passed": all_passed,
        "exams": results,
    }
    Path(args.json).write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("\n" + "-" * 78)
    for name, r in results.items():
        mark = "✅" if r["passed"] else "❌"
        brief = {k: v for k, v in r.items() if k != "passed"}
        print(f"{mark} {name}: {json.dumps(brief)[:220]}")
    print("-" * 78)
    print("REPORT:", args.json)
    print("🟢 PHASE-2 LIVE VALIDATION PASSED" if all_passed else "🔴 PHASE-2 LIVE VALIDATION FAILED")
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
