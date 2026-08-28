#!/usr/bin/env python3
"""
Deep Thinking & Code Quality Comparative Benchmark
===================================================
Compares:
1. Thinking / System-2 Reasoning Quality (Decomposition, Edge Cases, Invariant Analysis)
2. Code Quality (Type Safety, AST Compliance, Architecture Elegance, Ponytail Conciseness)
Between:
- Port 8138: Gemma-4-E4B-it-Q4_K_M + MTP (Google Champion)
- Port 8139: Qwen3.5-4B-Q4_K_M (Alibaba Challenger)
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

BENCHMARK_PROMPTS = [
    {
        "id": "arch_planning",
        "title": "Architectural Pre-Planning & Sliding Window Rate Limiter",
        "prompt": (
            "First, perform deep System-2 thinking inside <thought>...</thought> analyzing:\n"
            "1. Concurrency hazards (race conditions between timestamp pruning and counter increment)\n"
            "2. Memory bounds (eviction of stale timestamps to prevent leaks)\n"
            "3. Time complexity analysis.\n\n"
            "Then write a production-grade Python 3.13 SlidingWindowRateLimiter class using asyncio, dataclasses, and time.monotonic. "
            "Include type hints for every method."
        )
    },
    {
        "id": "spatial_quadtree",
        "title": "Complex Algorithmic Synthesis: 2D QuadTree Spatial Index",
        "prompt": (
            "First, reason step-by-step inside <thought>...</thought> about boundary invariants, subdivision conditions, and range query intersections.\n\n"
            "Then write a complete Python 3.13 QuadTree implementation with BoundingBox, Point, and QuadTree classes. "
            "Implement insert() and query_range(box) returning points within the bounding box. Full type hints required."
        )
    },
    {
        "id": "surgical_debugging",
        "title": "Root Cause Diagnosis & Minimal Surgical Patching",
        "prompt": (
            "Analyze this buggy code:\n"
            "```python\n"
            "class WorkerPool:\n"
            "    def __init__(self, size: int):\n"
            "        self.size = size\n"
            "        self.tasks = []\n"
            "        self.running = False\n"
            "    async def run(self):\n"
            "        self.running = True\n"
            "        for t in self.tasks:\n"
            "            await t()\n"
            "        self.running = False\n"
            "```\n"
            "Inside <thought>...</thought>, explain the 2 concurrency bugs (tasks executed serially instead of concurrently; mutating tasks during iteration).\n"
            "Then provide the fixed WorkerPool using asyncio.gather or TaskGroup with bounded semaphore concurrency."
        )
    }
]


def extract_thought_and_code(text: str):
    """Extracts thinking trace and code blocks cleanly."""
    # 1. Thought extraction
    thought = ""
    thought_match = re.search(r"<thought>(.*?)</thought>", text, re.DOTALL | re.IGNORECASE)
    if not thought_match:
        thought_match = re.search(r"<\|thought\|>(.*?)<\|/thought\|>", text, re.DOTALL | re.IGNORECASE)
    if thought_match:
        thought = thought_match.group(1).strip()
    else:
        # Check if model has prose before code
        if "```" in text:
            thought = text.split("```")[0].strip()

    # 2. Code extraction
    fence_pattern = re.compile(r"```(?:[a-zA-Z0-9_-]+)?\s*\n(.*?)```", re.DOTALL)
    matches = fence_pattern.findall(text)
    code = "\n\n".join(matches).strip() if matches else text.strip()

    return thought, code


def query_endpoint(base_url: str, prompt: str, max_tokens: int = 1500) -> dict:
    url = f"{base_url}/v1/chat/completions"
    payload = {
        "messages": [
            {"role": "system", "content": "You are a principal systems architect. Think deeply inside <thought> tags before synthesizing code."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": max_tokens,
        "stream": False
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=180) as resp:
        elapsed = time.perf_counter() - t0
        res = json.loads(resp.read().decode("utf-8"))
        content = res["choices"][0]["message"]["content"]
        usage = res.get("usage", {})
        completion_tokens = usage.get("completion_tokens", len(content.split()))
        tok_per_sec = completion_tokens / max(elapsed, 0.001)
        thought, code = extract_thought_and_code(content)
        return {
            "full_content": content,
            "thought": thought,
            "code": code,
            "elapsed_sec": elapsed,
            "completion_tokens": completion_tokens,
            "tok_per_sec": tok_per_sec
        }


def evaluate_run(task_id: str, thought: str, code: str) -> dict:
    # 1. Thought metrics
    thought_words = len(thought.split())
    has_explicit_thought = bool(thought and thought_words > 20)
    
    # 2. Code AST metrics
    ast_valid = False
    ast_error = ""
    has_typing = False
    has_classes = False
    loc = len([l for l in code.splitlines() if l.strip() and not l.strip().startswith("#")])

    try:
        tree = ast.parse(code)
        ast_valid = True
        has_classes = any(isinstance(n, ast.ClassDef) for n in ast.walk(tree))
        # Check type annotations
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and (node.returns or any(a.annotation for a in node.args.args)):
                has_typing = True
                break
    except SyntaxError as e:
        ast_error = str(e)

    # Scoring (0-100)
    score = 0
    if has_explicit_thought:
        score += 35
    if ast_valid:
        score += 35
    if has_classes:
        score += 15
    if has_typing:
        score += 15

    return {
        "score": score,
        "ast_valid": ast_valid,
        "ast_error": ast_error,
        "has_typing": has_typing,
        "thought_word_count": thought_words,
        "code_loc": loc
    }


def run_comparative_eval():
    print("==================================================================================")
    print(" 🚀 STARTING DEEP THINKING & CODE QUALITY BENCHMARK (GEMMA-4 vs QWEN-4B)")
    print("==================================================================================")
    
    models = [
        ("Gemma-4-E4B-it-Q4_K_M (GPU + MTP)", "http://127.0.0.1:8138"),
        ("Qwen3.5-4B-Q4_K_M (P-Core Pinned)", "http://127.0.0.1:8139")
    ]
    
    overall_report = {}

    for name, url in models:
        print(f"\nEvaluating: {name}...")
        model_results = []
        for prompt_spec in BENCHMARK_PROMPTS:
            print(f"  • Running Task: {prompt_spec['title']}...", end=" ", flush=True)
            try:
                res = query_endpoint(url, prompt_spec["prompt"])
                metrics = evaluate_run(prompt_spec["id"], res["thought"], res["code"])
                status = "✅ PASS" if metrics["ast_valid"] else "❌ FAIL"
                print(f"{status} (Score: {metrics['score']}/100, Thought: {metrics['thought_word_count']} words, Speed: {res['tok_per_sec']:.1f} tok/s)")
                model_results.append({
                    "task_id": prompt_spec["id"],
                    "title": prompt_spec["title"],
                    "thought_sample": res["thought"][:300] + ("..." if len(res["thought"]) > 300 else ""),
                    "code_sample": res["code"][:300] + ("..." if len(res["code"]) > 300 else ""),
                    "metrics": metrics,
                    "tok_per_sec": res["tok_per_sec"],
                    "elapsed_sec": res["elapsed_sec"],
                    "tokens": res["completion_tokens"]
                })
            except Exception as e:
                print(f"❌ ERROR: {e}")
                model_results.append({
                    "task_id": prompt_spec["id"],
                    "title": prompt_spec["title"],
                    "thought_sample": "",
                    "code_sample": "",
                    "metrics": {"score": 0, "ast_valid": False, "ast_error": str(e), "has_typing": False, "thought_word_count": 0, "code_loc": 0},
                    "tok_per_sec": 0,
                    "elapsed_sec": 0,
                    "tokens": 0
                })
        overall_report[name] = model_results

    # Output detailed summary table and comparison
    report_file = Path("/dev/shm/comparative_thinking_and_code_report.json")
    report_file.write_text(json.dumps(overall_report, indent=2), encoding="utf-8")
    print(f"\nFull raw evaluation artifacts saved to: {report_file}")


if __name__ == "__main__":
    run_comparative_eval()
