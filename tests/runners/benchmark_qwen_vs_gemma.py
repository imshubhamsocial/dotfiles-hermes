#!/usr/bin/env python3
"""
Precision Coding Benchmark: Qwen 4B vs Gemma-4-E4B Champion
===========================================================
Executes identical coding and reasoning challenges against:
- Port 8138: Gemma-4-E4B-it-Q4_K_M + MTP (GPU Accelerated)
- Port 8139: Qwen3.5-4B-Q4_K_M (Benchmarking Instance)
"""

import ast
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

BENCHMARK_TASKS = [
    {
        "id": "task_1_python_ast",
        "category": "Python AST & Type Annotations",
        "prompt": "Write a pure Python 3.13 module implementing a thread-safe EventBus with subscribe, unsubscribe, and publish methods using dataclasses and typing. Type hints mandatory. Emit only code inside a python block.",
        "eval_type": "python_ast"
    },
    {
        "id": "task_2_js_esm",
        "category": "JavaScript ES Module & Canvas LifeCycle",
        "prompt": "Write a standalone ES-module JavaScript class FluidWaveSimulation with double-buffered Float32Array velocity fields, step() PDE solver, and render(ctx). Must export default. Emit only code.",
        "eval_type": "js_esm"
    },
    {
        "id": "task_3_precision_math",
        "category": "Discrete Mathematical Proof & Precision",
        "prompt": "Find the sum of all prime numbers strictly between 100 and 200. List the primes and state the exact final integer sum.",
        "eval_type": "math"
    },
    {
        "id": "task_4_tool_schema_compliance",
        "category": "Google Tool Calling Schema Adherence",
        "prompt": "You need to replace lines 10 to 20 in app.py. Output a JSON object calling replace_file_content with TargetFile, StartLine, EndLine, TargetContent, ReplacementContent, toolAction, and toolSummary.",
        "eval_type": "json_schema"
    }
]


def extract_code_block(text: str, lang: str = "python") -> str:
    """Extract code from markdown fences if present, otherwise return cleaned text."""
    # Look for code fences
    fence_pattern = re.compile(r"```(?:[a-zA-Z0-9_-]+)?\s*\n(.*?)```", re.DOTALL)
    matches = fence_pattern.findall(text)
    if matches:
        return matches[0].strip()
    # Fallback: remove markdown comments
    lines = []
    for line in text.splitlines():
        if line.strip().startswith("```"):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def query_model(base_url: str, prompt: str, temperature: float = 0.0) -> dict:
    url = f"{base_url}/v1/chat/completions"
    payload = {
        "messages": [
            {"role": "system", "content": "You are an expert autonomous software engineer. Emit concise, mathematically precise, syntax-perfect code."},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": 2048,
        "stream": False
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=120) as resp:
        elapsed = time.perf_counter() - t0
        res = json.loads(resp.read().decode("utf-8"))
        content = res["choices"][0]["message"]["content"]
        usage = res.get("usage", {})
        completion_tokens = usage.get("completion_tokens", len(content.split()))
        tok_per_sec = completion_tokens / max(elapsed, 0.001)
        return {
            "content": content,
            "elapsed_sec": elapsed,
            "completion_tokens": completion_tokens,
            "tok_per_sec": tok_per_sec
        }


def evaluate_response(task: dict, response_text: str) -> dict:
    eval_type = task["eval_type"]
    clean_code = extract_code_block(response_text)

    if eval_type == "python_ast":
        try:
            tree = ast.parse(clean_code)
            has_class = any(isinstance(node, ast.ClassDef) for node in ast.walk(tree))
            return {"pass": has_class, "score": 100 if has_class else 50, "detail": "Valid Python AST parse"}
        except SyntaxError as e:
            return {"pass": False, "score": 0, "detail": f"Python SyntaxError: {e}"}

    elif eval_type == "js_esm":
        test_file = Path("/dev/shm/test_bench_eval.mjs")
        test_file.write_text(clean_code, encoding="utf-8")
        cmd = ["node", "--experimental-vm-modules", "-e",
               f"const fs = require('fs'); const vm = require('vm'); "
               f"const code = fs.readFileSync('{test_file}', 'utf8'); "
               f"new vm.SourceTextModule(code);"]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode == 0:
            return {"pass": True, "score": 100, "detail": "Valid JS ESM AST parse"}
        else:
            return {"pass": False, "score": 0, "detail": f"JS SyntaxError: {proc.stderr.strip()[:80]}"}

    elif eval_type == "math":
        primes = [101, 103, 107, 109, 113, 127, 131, 137, 139, 149, 151, 157, 163, 167, 173, 179, 181, 191, 193, 197, 199]
        expected_sum = sum(primes) # 3167
        has_sum = str(expected_sum) in response_text
        return {"pass": has_sum, "score": 100 if has_sum else 0, "detail": f"Sum=3167 in output: {has_sum}"}

    elif eval_type == "json_schema":
        has_action = "toolAction" in response_text
        has_summary = "toolSummary" in response_text
        has_file = "TargetFile" in response_text or "target_file" in response_text
        score = 100 if (has_action and has_summary and has_file) else (50 if (has_action or has_summary) else 0)
        return {"pass": score >= 50, "score": score, "detail": f"Schema fields (Action={has_action}, Summary={has_summary}, File={has_file})"}

    return {"pass": True, "score": 100, "detail": "Default pass"}


def run_benchmark(name: str, base_url: str) -> dict:
    print(f"\n==================================================================")
    print(f" 🔬 BENCHMARK RUN: {name}")
    print(f" URL: {base_url}")
    print(f"==================================================================")
    results = []
    total_tokens = 0
    total_time = 0.0

    for task in BENCHMARK_TASKS:
        print(f" • Testing [{task['id']}]: {task['category']}...", end=" ", flush=True)
        try:
            res = query_model(base_url, task["prompt"])
            eval_res = evaluate_response(task, res["content"])
            total_tokens += res["completion_tokens"]
            total_time += res["elapsed_sec"]
            status = "✅ PASS" if eval_res["pass"] else "❌ FAIL"
            print(f"{status} ({res['tok_per_sec']:.1f} tok/s) - {eval_res['detail']}")
            results.append({
                "task": task["id"],
                "category": task["category"],
                "eval": eval_res,
                "tok_per_sec": res["tok_per_sec"],
                "completion_tokens": res["completion_tokens"],
                "elapsed_sec": res["elapsed_sec"]
            })
        except Exception as e:
            print(f"❌ ERROR: {e}")
            results.append({
                "task": task["id"],
                "category": task["category"],
                "eval": {"pass": False, "score": 0, "detail": str(e)},
                "tok_per_sec": 0,
                "completion_tokens": 0,
                "elapsed_sec": 0
            })

    avg_speed = total_tokens / max(total_time, 0.001)
    pass_rate = (sum(1 for r in results if r["eval"]["pass"]) / len(results)) * 100
    avg_score = sum(r["eval"]["score"] for r in results) / len(results)

    return {
        "name": name,
        "base_url": base_url,
        "results": results,
        "pass_rate": pass_rate,
        "avg_score": avg_score,
        "avg_speed_tok_s": avg_speed,
        "total_tokens": total_tokens,
        "total_time_s": total_time
    }


if __name__ == "__main__":
    gemma_report = run_benchmark("Gemma-4-E4B-it-Q4_K_M + MTP (Production Champion)", "http://127.0.0.1:8138")
    qwen_report = run_benchmark("Qwen3.5-4B-Q4_K_M (Benchmarking Target)", "http://127.0.0.1:8139")

    print("\n" + "=" * 70)
    print(" 📊 HEAD-TO-HEAD PRECISION CODING BENCHMARK COMPARISON REPORT")
    print("=" * 70)
    print(f"┌───────────────────────────────┬──────────────────────┬──────────────────────┐")
    print(f"│ Metric                        │ Gemma-4-E4B (GPU)    │ Qwen-4B (Target)     │")
    print(f"├───────────────────────────────┼──────────────────────┼──────────────────────┤")
    print(f"│ **Overall Pass Rate**         │ {gemma_report['pass_rate']:>18.1f}% │ {qwen_report['pass_rate']:>18.1f}% │")
    print(f"│ **Average Quality Score**     │ {gemma_report['avg_score']:>17.1f}/100│ {qwen_report['avg_score']:>17.1f}/100│")
    print(f"│ **Average Speed (tok/s)**     │ {gemma_report['avg_speed_tok_s']:>14.1f} tok/s│ {qwen_report['avg_speed_tok_s']:>14.1f} tok/s│")
    print(f"│ **Total Generated Tokens**    │ {gemma_report['total_tokens']:>18} tok│ {qwen_report['total_tokens']:>18} tok│")
    print(f"└───────────────────────────────┴──────────────────────┴──────────────────────┘")
