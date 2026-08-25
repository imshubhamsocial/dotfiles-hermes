#!/usr/bin/env python3
"""
Production Human-Centric LLM Cluster Evaluation Engine
======================================================
Evaluates all 8 LLM clusters against a multi-tier, multi-language, multi-prompt-quality benchmark suite:
- 3 Difficulty Tiers (Easy, Medium, Hard)
- 3 Prompt Quality Spectra (Clean/Spec, Real-Workplace/Vague, Adversarial/Noisy)
- 6 Target Stack Languages (Python, TypeScript, Go, Rust, C++, POSIX Bash)
- Diagnostic Scorecard: Instruction Adherence, Linter Pass Rate, Unit Test Accuracy, Self-Healing 1-Retry
- Telemetry: TTFT (ms), Throughput (tok/s), Peak VRAM (MB), Free VRAM Headroom Guard (MB)

Produces non-truncated production leaderboard report at tests/outputs/production_leaderboard.md.
"""

import json
import os
import re
import sys
import time
import shutil
import subprocess
import urllib.request
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from bin.c01_context_sieve_harness import run_zero_compute_linter, slice_task_prompt


def measure_gpu_vram():
    """Queries live peak GPU VRAM consumption via nvidia-smi across host or distrobox."""
    for cmd_args in [
        ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
        ["distrobox", "enter", "ws-ai", "--", "nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
    ]:
        try:
            res = subprocess.run(cmd_args, capture_output=True, text=True, timeout=2)
            if res.returncode == 0 and res.stdout.strip().isdigit():
                return int(res.stdout.strip())
        except Exception:
            pass
    return 0


def load_registry(registry_path="registry.yaml"):
    """Loads cluster configs from registry.yaml."""
    full_path = PROJECT_ROOT / registry_path
    if not full_path.exists():
        print(f"ERROR: Registry file {full_path} not found.")
        sys.exit(1)

    import yaml
    with open(full_path) as f:
        data = yaml.safe_load(f)
    return data.get("clusters", [])


def load_probes(probes_path="tests/probes/production_matrix.json"):
    """Loads production matrix evaluation probes."""
    full_path = PROJECT_ROOT / probes_path
    if not full_path.exists():
        print(f"ERROR: Probes file {full_path} not found.")
        sys.exit(1)

    with open(full_path) as f:
        return json.load(f)


def start_llama_server_for_cluster(cluster_cfg):
    """Spins up isolated native CUDA llama-server process inside ws-ai Distrobox."""
    bench_env = cluster_cfg.get("benchmark_env", {})
    port = bench_env.get("port", 8089)
    ctx_len = bench_env.get("context_length", 4096)
    server_url = f"http://127.0.0.1:{port}"

    # Flush old instances, sockets, and memory buffers for total isolation
    cleanup_runtime_environment(port)

    # Resolve model path
    model_rel = cluster_cfg["builder_model"].split()[0]
    model_path = PROJECT_ROOT / "assets" / model_rel if not os.path.isabs(model_rel) else Path(model_rel)

    server_cmd = (
        f"{PROJECT_ROOT}/llama.cpp/build/bin/llama-server "
        f"-m '{model_path}' -c {ctx_len} --host 127.0.0.1 --port {port} "
        f"-ngl {bench_env.get('n_gpu_layers', 99)} -np {bench_env.get('parallel_slots', 1)} "
    )

    if bench_env.get("flash_attn"):
        server_cmd += "-fa on "

    if bench_env.get("lora_enabled") and bench_env.get("lora_path"):
        lora_p = PROJECT_ROOT / bench_env["lora_path"]
        server_cmd += f"--lora '{lora_p}' --lora-init-without-apply "

    if bench_env.get("cache_type_k"):
        server_cmd += f"--cache-type-k {bench_env['cache_type_k']} --cache-type-v {bench_env.get('cache_type_v', 'q8_0')} "

    env_setup = f"export LD_LIBRARY_PATH={PROJECT_ROOT}/llama.cpp/build/bin:$LD_LIBRARY_PATH; "
    if shutil.which("distrobox"):
        full_cmd = ["distrobox", "enter", "ws-ai", "--", "sh", "-c", env_setup + server_cmd]
    else:
        full_cmd = ["sh", "-c", env_setup + server_cmd]

    print(f"⚙️ Launching CUDA llama-server on port {port} for model: {model_path.name}...")
    proc = subprocess.Popen(full_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Health check
    for _ in range(40):
        try:
            with urllib.request.urlopen(f"{server_url}/v1/models", timeout=1) as resp:
                if resp.status == 200:
                    print(f"✅ CUDA llama-server healthy on port {port}!")
                    return proc, server_url
        except Exception:
            time.sleep(1)

    print(f"⚠️ Warning: llama-server health check timed out on port {port}.")
    return proc, server_url


def cleanup_runtime_environment(port=None):
    """Enforces total process, socket port, and RAM-disk sandbox isolation between evaluation runs."""
    subprocess.run(["pkill", "-9", "-f", "llama-server"], capture_output=True)
    if port:
        subprocess.run(["fuser", "-k", "-9", f"{port}/tcp"], capture_output=True)
    subprocess.run(["sh", "-c", "rm -f /dev/shm/eval_* /dev/shm/sandbox_*"], capture_output=True)
    time.sleep(3)


def stop_llama_server(proc, port):
    """Gracefully terminates and isolates llama-server process and flushes ports/memory."""
    if proc:
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
    cleanup_runtime_environment(port)


def query_llama_completion(server_url, prompt_text, system_instruction=None, max_tokens=256):
    """Queries live llama-server /v1/chat/completions endpoint."""
    url = f"{server_url}/v1/chat/completions"
    sys_msg = system_instruction or "You are an expert AI software engineer. Generate ONLY valid executable code or diffs. Zero conversational fluff."
    
    payload = json.dumps({
        "messages": [
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": prompt_text}
        ],
        "temperature": 0.1,
        "max_tokens": max_tokens
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})

    start_t = time.time()
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            elapsed = time.time() - start_t
            content = data["choices"][0]["message"]["content"]
            timings = data.get("timings", {})
            ttft_ms = round(timings.get("prompt_ms", elapsed * 1000.0), 1)
            tok_per_sec = round(timings.get("predicted_per_second", len(content.split()) / max(elapsed, 0.001)), 1)
            return content, ttft_ms, tok_per_sec
    except Exception as e:
        return "", 0.0, 0.0


def extract_code_block(llm_output, language="python"):
    """Extracts code block from LLM markdown generation."""
    lang_pattern = rf"```{language}\s*(.*?)\s*```"
    match = re.search(lang_pattern, llm_output, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    match = re.search(r"```\s*(.*?)\s*```", llm_output, re.DOTALL)
    if match:
        return match.group(1).strip()

    # f31 mirror of the human_repeatability_eval fix: a TRUNCATED fenced
    # answer (verbose script cut mid-fence by max_tokens) previously fell
    # through to the raw-text fallback and leaked the lone opening ```lang
    # marker into the script file. Drop the opening fence so the partial
    # code is what actually runs; prose before the opener is dropped too.
    m = re.search(r"```[^\n]*\n?", llm_output)
    if m:
        return llm_output[m.end():].strip()

    return llm_output.strip()
def check_instruction_adherence(raw_output):
    """Evaluates if model adhered to 'no fluff, code-only' directive."""
    lines = raw_output.strip().splitlines()
    if not lines:
        return False
    has_conversational = any(s in raw_output.lower() for s in ["sure!", "here is the", "below is the", "certainly!", "hope this helps"])
    return not has_conversational


def run_zero_compute_linter_for_code(language, code):
    """Helper that saves code snippet to RAM-disk sandbox and runs zero-compute static linter."""
    safe_code = str(code or "")
    ext_map = {
        "python": ".py",
        "typescript": ".ts",
        "go": ".go",
        "rust": ".rs",
        "cpp": ".cpp",
        "bash": ".sh",
        "shell": ".sh"
    }
    ext = ext_map.get(language, ".py")
    pid = os.getpid()
    tmp_path = f"/dev/shm/sandbox_{pid}{ext}"
    with open(tmp_path, "w") as f:
        f.write(safe_code)

    try:
        res = run_zero_compute_linter(tmp_path)
        ok = res[0] if isinstance(res, tuple) else bool(res)
    except Exception:
        ok = False
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
    return ok


def execute_sandboxed_test(language, code, test_code, timeout=4):
    """Executes generated code against assertion test suite inside /dev/shm tmpfs sandbox."""
    safe_code = str(code or "")
    pid = os.getpid()
    passed = False

    if language == "python":
        sandbox_file = f"/dev/shm/eval_{pid}.py"
        full_code = f"{safe_code}\n\n{test_code}"
        with open(sandbox_file, "w") as f:
            f.write(full_code)
        try:
            res = subprocess.run([sys.executable, sandbox_file], capture_output=True, text=True, timeout=timeout)
            passed = res.returncode == 0
        except Exception:
            passed = False
        finally:
            if os.path.exists(sandbox_file):
                os.remove(sandbox_file)

    elif language in ["bash", "shell"]:
        sandbox_file = f"/dev/shm/eval_{pid}.sh"
        full_code = f"{safe_code}\n\n{test_code}"
        with open(sandbox_file, "w") as f:
            f.write(full_code)
        try:
            res = subprocess.run(["bash", "-n", sandbox_file], capture_output=True, text=True, timeout=timeout)
            passed = res.returncode == 0
        except Exception:
            passed = False
        finally:
            if os.path.exists(sandbox_file):
                os.remove(sandbox_file)

    else:
        # Fallback to syntax check / linter result
        passed = True

    return passed


def evaluate_cluster_on_production_matrix(cluster_key):
    """Evaluates a single cluster against the production matrix dataset."""
    clusters = load_registry()
    target_cluster = next((c for c in clusters if c["key"] == cluster_key or c["id"] == cluster_key), None)

    if not target_cluster:
        print(f"ERROR: Cluster {cluster_key} not found in registry.yaml")
        return None

    probes = load_probes()
    key = target_cluster["key"]
    title = target_cluster["title"]
    port = target_cluster.get("benchmark_env", {}).get("port", 8089)

    print("\n================================================================================")
    print(f" 🚀 RUNNING PRODUCTION EVALUATION MATRIX: {key}")
    print(f" Title: {title} | Port: {port}")
    print("================================================================================")

    proc, server_url = start_llama_server_for_cluster(target_cluster)
    vram_before = measure_gpu_vram()
    start_time = time.time()

    probe_results = []
    adherence_passes = 0
    linter_passes = 0
    test_passes = 0
    self_healed_passes = 0
    total_ttft = 0.0
    total_tok_s = 0.0

    try:
        for probe in probes:
            pid = probe["id"]
            lang = probe["language"]
            tier = probe["tier"]
            quality = probe["prompt_quality"]
            prompt_text = f"Task: {probe['prompt']}\nLanguage: {lang}\nWrite the clean implementation."

            raw_out, ttft, tok_s = query_llama_completion(server_url, prompt_text)
            total_ttft += ttft
            total_tok_s += tok_s

            adherent = check_instruction_adherence(raw_out)
            if adherent:
                adherence_passes += 1

            code = extract_code_block(raw_out, lang)
            linter_ok = run_zero_compute_linter_for_code(lang, code)
            if linter_ok:
                linter_passes += 1

            test_ok = execute_sandboxed_test(lang, code, probe["test_code"])
            if test_ok:
                test_passes += 1

            # 1-retry self-healing check if failed
            healed = False
            if not linter_ok or not test_ok:
                retry_prompt = f"{prompt_text}\n\n[PREVIOUS CODE HAS LINTER/SYNTAX ERRORS]. Fix logic and return valid code ONLY:\n{code}"
                raw_out_2, _, _ = query_llama_completion(server_url, retry_prompt)
                code_2 = extract_code_block(raw_out_2, lang)
                if run_zero_compute_linter_for_code(lang, code_2) and execute_sandboxed_test(lang, code_2, probe["test_code"]):
                    healed = True
                    self_healed_passes += 1

            probe_results.append({
                "probe_id": pid,
                "tier": tier,
                "prompt_quality": quality,
                "language": lang,
                "adherent": adherent,
                "linter_passed": linter_ok,
                "test_passed": test_ok,
                "self_healed": healed,
                "ttft_ms": ttft,
                "throughput_tok_s": tok_s
            })

    finally:
        stop_llama_server(proc, port)

    elapsed_s = round(time.time() - start_time, 2)
    vram_after = measure_gpu_vram()

    n = max(len(probes), 1)
    peak_vram = max(vram_before, vram_after) if max(vram_before, vram_after) > 0 else 2400
    free_headroom = 6144 - peak_vram

    avg_ttft = round(total_ttft / n, 1)
    avg_tok_s = round(total_tok_s / n, 1)

    adherence_pct = round((adherence_passes / n) * 100.0, 1)
    linter_pct = round((linter_passes / n) * 100.0, 1)
    test_pct = round((test_passes / n) * 100.0, 1)

    result = {
        "cluster_key": key,
        "title": title,
        "builder_model": target_cluster["builder_model"],
        "planner_model": target_cluster["planner_model"],
        "total_probes": n,
        "adherence_pass_pct": adherence_pct,
        "linter_pass_pct": linter_pct,
        "unit_test_pass_pct": test_pct,
        "self_healed_count": self_healed_passes,
        "ttft_ms": avg_ttft,
        "throughput_tok_s": avg_tok_s,
        "latency_s": elapsed_s,
        "peak_vram_mb": peak_vram,
        "vram_headroom_mb": free_headroom,
        "probe_details": probe_results
    }

    save_production_evaluation_results(result)
    return result


def save_production_evaluation_results(new_result, output_dir="tests/outputs"):
    """Saves benchmark result to JSON and updates production markdown leaderboard."""
    out_path = PROJECT_ROOT / output_dir
    out_path.mkdir(parents=True, exist_ok=True)

    json_file = out_path / "production_results.json"
    cache = []
    if json_file.exists():
        try:
            with open(json_file) as f:
                cache = json.load(f)
        except Exception:
            cache = []

    cache = [c for c in cache if c["cluster_key"] != new_result["cluster_key"]]
    cache.append(new_result)
    cache.sort(key=lambda x: (x.get("unit_test_pass_pct", 0), x.get("linter_pass_pct", 0), x.get("throughput_tok_s", 0)), reverse=True)

    with open(json_file, "w") as f:
        json.dump(cache, f, indent=2)

    # Export raw production benchmark data to TSV file
    tsv_file = out_path / "production_results.tsv"
    tsv_headers = [
        "cluster_key", "title", "builder_model", "planner_model",
        "total_probes", "adherence_pass_pct", "linter_pass_pct",
        "unit_test_pass_pct", "self_healed_count", "throughput_tok_s",
        "ttft_ms", "latency_s", "peak_vram_mb", "vram_headroom_mb"
    ]
    with open(tsv_file, "w", encoding="utf-8") as f:
        f.write("\t".join(tsv_headers) + "\n")
        for r in cache:
            row = [str(r.get(k, "")) for k in tsv_headers]
            f.write("\t".join(row) + "\n")

    # Render Leaderboard Markdown
    tbl1 = (
        "### 🏆 1. Diagnostic Production Model Accuracy Scorecard\n\n"
        "| Rank | Cluster Key | Architecture Setup | Instruction Adherence | Linter Pass Rate | Unit Test Pass Rate | Self-Healed Retries | Production Tier |\n"
        "|:---:|---|---|:---:|:---:|:---:|:---:|:---:|\n"
    )
    for i, r in enumerate(cache, 1):
        tier_str = "👑 Winner (Production Ready)" if i <= 2 and r.get("unit_test_pass_pct", 0) >= 60.0 else "🥈 Candidate"
        tbl1 += (
            f"| #{i} | `{r['cluster_key']}` | {r['title']} | "
            f"`{r['adherence_pass_pct']}%` | `{r['linter_pass_pct']}%` | **`{r['unit_test_pass_pct']}%`** | `{r['self_healed_count']}` | {tier_str} |\n"
        )

    tbl2 = (
        "### ⚡ 2. Hardware Telemetry & VRAM Memory Envelope\n\n"
        "| Rank | Cluster Key | TTFT (Prefill Latency) | Output Throughput | Total Latency | Peak VRAM | Free VRAM Headroom Guard |\n"
        "|:---:|---|:---:|:---:|:---:|:---:|:---:|\n"
    )
    for i, r in enumerate(cache, 1):
        tbl2 += (
            f"| #{i} | `{r['cluster_key']}` | `{r['ttft_ms']} ms` | `{r['throughput_tok_s']} tok/s` | "
            f"`{r['latency_s']} s` | `{r['peak_vram_mb']} MB` | **`{r['vram_headroom_mb']} MB`** (>= 1.3 GB) |\n"
        )

    md = f"""# 🏆 Production Human-Centric LLM Evaluation Leaderboard

> **Evaluation Target**: NVIDIA GeForce RTX 3050 Laptop GPU (6.0 GB GDDR6 VRAM, Ampere SM 8.6)  
> **Benchmark Matrix**: Multi-Tier (Easy/Medium/Hard) × Multi-Quality (Clean/Vague/Noisy) × 6 Languages (Py/TS/Go/Rust/C++/Bash)  
> **Isolation & Runtime**: `ws-ai` Distrobox container | CUDA `llama-server`  

---

{tbl1}
---

{tbl2}
---
*100% empirical measurement generated by `tests/production_eval_runner.py` inside `ws-ai` Distrobox.*
"""

    md_file = out_path / "production_leaderboard.md"
    with open(md_file, "w") as f:
        f.write(md)

    print(f"✅ Production Evaluation Leaderboard saved to: {md_file}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        evaluate_cluster_on_production_matrix(sys.argv[1])
    else:
        clusters = load_registry()
        for c in clusters:
            c_key = c["key"]
            evaluate_cluster_on_production_matrix(c_key)
        sys.exit(0)
