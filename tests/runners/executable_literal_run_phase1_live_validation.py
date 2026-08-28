#!/usr/bin/env python3
"""
Phase-1 Live GPU Validation (RTX 3050 / Gemma 4-E4B + MTP @ :8138)
==================================================================
The honest external arbiter for the offline contract spike:

  Exam A (U1 Code Mode): Gemma emits ONE linear batch script (SDK methods
          only); we extract deterministically (bin/extract_code_mode.py),
          execute it against a buggy artifact, and enforce the roadmap's
          sub-25s EXECUTION budget. Records tok/s incl. MTP effect.
  Exam B (U9 Minimal Preset): minimal system prompt + bash-only runtime;
          3 probe questions must be answered WITHOUT invoking ghost tools.
  Exam C (VRAM guard): server must stay within the 4.7 GB envelope.

Usage: python3 bin/run_phase1_live_validation.py [--json OUT]
Exit 0 = all exams passed.
"""

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / ".hermes" / "src"))

BASE_URL = "http://localhost:8138/v1"
WORKDIR = Path("/dev/shm/hermes_live")
SDK_DIR = ROOT / "ws-ai" / "sdk"
EXEC_BUDGET_S = 25.0
VRAM_BUDGET_MIB = 4812  # 4.7 GB

GHOST_TOOLS = ["web_search", "read_symbol", "get_workspace_tree", "query_knowledge_graph", "refactor_symbol"]

BUGGY_HTML = """<html><body><script>
function render() {
  const x = {a:1
  return x;
}
window.render = render;
</script></body></html>
"""


def healthy():
    try:
        with urllib.request.urlopen("http://localhost:8138/health", timeout=2) as r:
            return json.loads(r.read()).get("status") == "ok"
    except Exception:
        return False


def vram_used_mib():
    out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                         capture_output=True, text=True).stdout.strip().splitlines()[0]
    return int(out)


def chat(client, messages, max_tokens=512):
    t0 = time.time()
    resp = client.chat.completions.create(
        model=[m.id for m in client.models.list().data][0],
        messages=messages,
        temperature=1.0, top_p=0.95, max_tokens=max_tokens,
        extra_body={"top_k": 64, "min_p": 0.0},
    )
    dt = time.time() - t0
    u = resp.usage
    text = resp.choices[0].message.content or ""
    tps = (u.completion_tokens / dt) if dt > 0 else 0.0
    return text, {"gen_s": round(dt, 2), "completion_tokens": u.completion_tokens, "tok_per_s": round(tps, 1)}


def exam_a_code_mode(client):
    WORKDIR.mkdir(parents=True, exist_ok=True)
    (WORKDIR / "build_probe.html").write_text(BUGGY_HTML, encoding="utf-8")

    prompt = f"""You are @coder in Code Mode. Emit ONLY a python script (no prose, no markdown fences).
Rules: max 12 lines, flat linear pipeline, use ONLY these calls on the sdk object below.
The bug: line 'const x = {{a:1' is missing its closing brace+semicolon.

Script template to complete exactly:
import os
os.environ["HERMES_SDK_WORKSPACE"] = "{WORKDIR}"
import sys
sys.path.insert(0, "{SDK_DIR}")
from hermes_sdk import sdk
sdk.read_range("build_probe.html", 1, 8)
sdk.apply_patch("build_probe.html", "const x = {{a:1", "const x = {{a:1}};")
sdk.run_observer_gate("build_probe.html")
r = sdk.run_test("grep -c 'window.render' build_probe.html")
print("CODE_MODE_DONE", r["passed"])

Output the completed script now."""

    raw, gen_stats = chat(client, [{"role": "user", "content": prompt}], max_tokens=900)

    # Gemma 4 dual-channel: strip native thought channel before extraction.
    raw = re.sub(r"<\|channel>thought.*?<channel\|>", "", raw, flags=re.S)
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.S)

    from bin.extract_code_mode import extract_code_validated
    try:
        code = extract_code_validated(raw)
    except ValueError as e:
        return {"exam": "A_u1_code_mode", "passed": False,
                "reason": f"extraction failed: {e}", **gen_stats}
    if "apply_patch" not in code:
        return {"exam": "A_u1_code_mode", "passed": False,
                "reason": "emitted script incomplete (truncation?) - no apply_patch call",
                "raw_tail": raw[-200:], **gen_stats}

    (WORKDIR / "build_probe.html").write_text(BUGGY_HTML, encoding="utf-8")  # reset bug
    env_path = WORKDIR / "emitted_batch.py"
    env_path.write_text(code, encoding="utf-8")

    t0 = time.time()
    res = subprocess.run([sys.executable, str(env_path)], capture_output=True, text=True, timeout=60)
    exec_s = time.time() - t0

    fixed = "const x = {a:1};" in (WORKDIR / "build_probe.html").read_text()
    passed = res.returncode == 0 and "CODE_MODE_DONE True" in res.stdout and fixed and exec_s < EXEC_BUDGET_S
    return {
        "exam": "A_u1_code_mode",
        "passed": passed,
        "exec_s": round(exec_s, 2),
        "budget_s": EXEC_BUDGET_S,
        "artifact_fixed": fixed,
        "exit_code": res.returncode,
        "stdout_tail": res.stdout.strip()[-120:],
        "stderr_tail": res.stderr.strip()[-200:] if res.returncode else "",
        **gen_stats,
    }


def exam_b_minimal_preset(client):
    from hermes_core.presets import MINIMAL_SYSTEM_PROMPT, estimate_prompt_tokens
    probes = [
        ("List the tools available to you right now.", None),
        ("Use grep to count occurrences of 'render' in your instructions. Answer with just the number.", None),
        ("What is 17*23? Answer with the number only.", None),
    ]
    results, clean = [], True
    for q, _ in probes:
        text, _stats = chat(client, [
            {"role": "system", "content": MINIMAL_SYSTEM_PROMPT},
            {"role": "user", "content": q},
        ], max_tokens=200)
        ghosts = [g for g in GHOST_TOOLS if g in text]
        ok = not ghosts
        clean &= ok
        results.append({"q": q[:40], "ghost_tools_named": ghosts, "answer_head": text.strip()[:80]})
    return {
        "exam": "B_u9_minimal_preset",
        "passed": clean,
        "prompt_tokens_est": estimate_prompt_tokens(MINIMAL_SYSTEM_PROMPT),
        "probes": results,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default="/dev/shm/hermes_live/verdict.json")
    args = ap.parse_args()

    if not healthy():
        print(json.dumps({"passed": False, "error": "llama-server :8138 not healthy"}))
        sys.exit(1)

    from openai import OpenAI
    client = OpenAI(base_url=BASE_URL, api_key="local")

    vr = vram_used_mib()
    a = exam_a_code_mode(client)
    b = exam_b_minimal_preset(client)
    c = {"exam": "C_vram_guard", "passed": vr <= VRAM_BUDGET_MIB, "vram_mib": vr, "budget_mib": VRAM_BUDGET_MIB}

    verdict = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "server_model": "gemma-4-E4B-it-Q4_K_M + MTP drafter",
        "exams": [a, b, c],
        "passed": all(e["passed"] for e in [a, b, c]),
    }
    Path(args.json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json).write_text(json.dumps(verdict, indent=2), encoding="utf-8")
    print(json.dumps(verdict, indent=2))
    sys.exit(0 if verdict["passed"] else 1)


if __name__ == "__main__":
    main()
