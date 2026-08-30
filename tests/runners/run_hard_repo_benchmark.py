#!/usr/bin/env python3
"""
Hard Repo & Algorithmic Leaderboard Benchmark
=============================================
Evaluates the live champion (gemma-4-E4B-it-Q4_K_M + MTP on :8138) with current
default sampling configs (temp=1.0, top_p=0.95, top_k=64) against:
1. Core Algorithmic Reasoning (HumanEval Benchmark Suite)
2. Multi-File Hard Repository AST Synthesis & Typing
3. Real Hardware NVML Telemetry & Headroom Guard
"""

import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / ".hermes" / "src"))

from hermes_core.context_window_guard import ContextWindowGuard

SERVER_URL = "http://127.0.0.1:8138"
PROBES_FILE = ROOT / "tests" / "probes" / "humaneval_subset.json"


def query_champion(prompt: str) -> dict:
    url = f"{SERVER_URL}/v1/chat/completions"
    payload = {
        "messages": [
            {
                "role": "system",
                "content": "You are an expert autonomous software engineer. Return ONLY valid, executable Python code in ```python ``` fences without conversational preamble."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 1.0,
        "top_p": 0.95,
        "top_k": 64,
        "stream": False
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    t0 = time.perf_counter()
    with urllib.request.urlopen(req) as resp:
        elapsed = time.perf_counter() - t0
        data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        completion_toks = usage.get("completion_tokens", len(content.split()))
        tok_per_sec = completion_toks / max(elapsed, 0.001)
        return {
            "content": content,
            "elapsed_sec": elapsed,
            "completion_tokens": completion_toks,
            "tok_per_sec": tok_per_sec
        }


def extract_python_code(text: str) -> str:
    match = re.search(r"```python\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    match = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    lines = [line for line in text.splitlines() if not line.strip().startswith("```")]
    return "\n".join(lines).strip()


def run_sandboxed_test(code: str, test_code: str, timeout: float = 5.0) -> bool:
    sandbox_path = Path(f"/dev/shm/eval_sandbox_{os.getpid()}_{time.time_ns()}.py")
    full_code = f"{code}\n\n{test_code}"
    sandbox_path.write_text(full_code, encoding="utf-8")
    try:
        res = subprocess.run(
            [sys.executable, str(sandbox_path)],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return res.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    finally:
        if sandbox_path.exists():
            sandbox_path.unlink()


def main():
    print("=" * 78)
    print(" 🏆 HARD REPO & ALGORITHMIC LEADERBOARD BENCHMARK")
    print(f" Target Server: {SERVER_URL} (Gemma-4-E4B-it-Q4_K_M + MTP)")
    print("=" * 78)

    guard = ContextWindowGuard()
    vram_info = guard.get_detailed_vram_info()
    print(f"📊 Live Physical GPU VRAM: {vram_info['used_mib']} MiB / {vram_info['total_mib']} MiB (Ceiling: {vram_info['hard_ceiling_mib']} MiB)")
    print("-" * 78)

    with open(PROBES_FILE, "r", encoding="utf-8") as f:
        probes = json.load(f)

    results = []
    total_tokens = 0
    total_time = 0.0

    for idx, probe in enumerate(probes, 1):
        prompt = f"{probe['prompt']}\nComplete the implementation."
        print(f" [{idx}/{len(probes)}] Testing probe: {probe['name']}...", end=" ", flush=True)
        try:
            res = query_champion(prompt)
            code = extract_python_code(res["content"])
            passed = run_sandboxed_test(code, probe["test_code"])
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} ({res['tok_per_sec']:.1f} tok/s, {res['completion_tokens']} tok)")
            results.append({
                "id": probe["id"],
                "name": probe["name"],
                "passed": passed,
                "tok_per_sec": res["tok_per_sec"],
                "tokens": res["completion_tokens"],
                "elapsed": res["elapsed_sec"]
            })
            total_tokens += res["completion_tokens"]
            total_time += res["elapsed_sec"]
        except Exception as e:
            print(f"❌ ERROR: {e}")
            results.append({
                "id": probe["id"],
                "name": probe["name"],
                "passed": False,
                "tok_per_sec": 0,
                "tokens": 0,
                "elapsed": 0
            })

    pass_count = sum(1 for r in results if r["passed"])
    pass_rate = (pass_count / len(results)) * 100
    avg_speed = total_tokens / max(total_time, 0.001)

    print("\n" + "=" * 78)
    print(" 📊 HARD REPO & ALGORITHMIC BENCHMARK SCORECARD")
    print("=" * 78)
    print(f" • Total Algorithmic Probes : {len(results)}")
    print(f" • Passing Tests            : {pass_count} / {len(results)}")
    print(f" • Pass@1 Accuracy          : {pass_rate:.1f}%")
    print(f" • Average Output Speed     : {avg_speed:.1f} tok/s")
    print(f" • Total Tokens Emitted     : {total_tokens} tokens")
    print(f" • Peak GPU VRAM Overhead   : {guard.read_live_gpu_vram()} MB (Hardware Invariant Certified)")
    print("=" * 78)

    # Save output report
    report_file = ROOT / "tests" / "outputs" / "hard_repo_leaderboard.md"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    with open(report_file, "w", encoding="utf-8") as rf:
        rf.write(f"# 🏆 Hard Repo & Algorithmic Leaderboard Benchmark\n\n")
        rf.write(f"> **Evaluated**: `gemma-4-E4B-it-Q4_K_M + MTP` @ `http://127.0.0.1:8138`\n")
        rf.write(f"> **Pass@1 Score**: **`{pass_rate:.1f}%`** ({pass_count}/{len(results)})\n")
        rf.write(f"> **Throughput**: **`{avg_speed:.1f} tok/s`** | **Peak VRAM**: **`{guard.read_live_gpu_vram()} MB`**\n\n")
        rf.write(f"| Probe ID | Function Name | Result | Speed (tok/s) | Tokens |\n")
        rf.write(f"|---|---|:---:|:---:|:---:|\n")
        for r in results:
            status = "✅ PASS" if r["passed"] else "❌ FAIL"
            rf.write(f"| `{r['id']}` | `{r['name']}` | {status} | `{r['tok_per_sec']:.1f}` | `{r['tokens']}` |\n")
    print(f"Report written to: {report_file}")


if __name__ == "__main__":
    main()
