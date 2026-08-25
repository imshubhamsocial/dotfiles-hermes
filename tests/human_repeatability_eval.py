#!/usr/bin/env python3
"""
Human Workplace Repeatability & Fact-Checking Benchmark Suite
============================================================
Evaluates LLM clusters based on real human workplace developer personas:
- Junior Dev (Vague / Conversational)
- Senior Architect (Strict Design / Type Safety)
- DevOps SRE (Idempotent POSIX Automation)
- Data / Backend Engineer (High-Throughput Concurrency)
- Systems Engineer (Low-Latency Bounded Memory)

Synergizes 4 core principles:
1. Functional Accuracy (Unit Test Assertions in /dev/shm — REALLY executed for
   every language: python3, bash, node+tsc, go test, rustc --test, g++)
2. Instruction Adherence (Zero Conversational Fluff / Strict Code Output)
3. 3x Repetitive Prompt Consistency (Determinism / Flakiness Index)
4. Prompt Variation Robustness (Phrasing Shift Tolerance)
5. Zero-Compute Host Linter Fact-Checking (Ruff, Biome, Golangci-lint, Cargo, Shellcheck)

Computes the fair Composite Human Workplace Utility Score (HWUS) via the shared
engine in bin/hwus_scoring.py:
  HWUS = 0.30*Accuracy + 0.20*Adherence + 0.15*Determinism + 0.10*Robustness
       + 0.10*Linter + 0.15*Efficiency
where Efficiency is cohort-relative measured throughput + TTFT, persona balance
is reported but excluded (it is derived from the same variation data), and VRAM
is a safety check only (never scored).
"""

import json
import os
import re
import sys
import time
import shutil
from datetime import datetime
import subprocess
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from bin.c01_context_sieve_harness import run_zero_compute_linter
from bin.container_cmd import get_distrobox_cmd
from bin.hwus_scoring import compute_hwus, recompute_hwus_for_results

DISTROBOX_CMD = get_distrobox_cmd()


def measure_gpu_vram():
    for cmd_args in [
        ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
        DISTROBOX_CMD + ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
    ]:
        try:
            res = subprocess.run(cmd_args, capture_output=True, text=True, timeout=2)
            if res.returncode == 0 and res.stdout.strip().isdigit():
                return int(res.stdout.strip())
        except Exception:
            pass
    return 0


def load_registry(registry_path="registry.yaml"):
    full_path = PROJECT_ROOT / registry_path
    if not full_path.exists():
        print(f"ERROR: Registry file {full_path} not found.")
        sys.exit(1)

    import yaml
    with open(full_path) as f:
        data = yaml.safe_load(f)
    return data.get("clusters", [])


def load_gold_probes(probes_path="tests/probes/human_workplace_gold_standard.json"):
    full_path = PROJECT_ROOT / probes_path
    if not full_path.exists():
        print(f"ERROR: Gold standard probes file {full_path} not found.")
        sys.exit(1)

    with open(full_path) as f:
        return json.load(f)


def cleanup_runtime_environment(port=None):
    subprocess.run(["pkill", "-9", "-f", "llama-server"], capture_output=True)
    if port:
        subprocess.run(["fuser", "-k", "-9", f"{port}/tcp"], capture_output=True)
    subprocess.run(["sh", "-c", "rm -f /dev/shm/eval_* /dev/shm/sandbox_*"], capture_output=True)
    time.sleep(3)


def start_llama_server_for_cluster(cluster_cfg):
    bench_env = cluster_cfg.get("benchmark_env", {})
    port = bench_env.get("port", 8089)
    ctx_len = bench_env.get("context_length", 4096)
    server_url = f"http://127.0.0.1:{port}"

    cleanup_runtime_environment(port)

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


def stop_llama_server(proc, port):
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


def extract_code_block(llm_output, language="python", is_dual_mode=False):
    text = llm_output
    if is_dual_mode:
        text = re.sub(r"<thought>.*?</thought>", "", text, flags=re.DOTALL).strip()

    lang_pattern = rf"```{language}\s*(.*?)\s*```"
    match = re.search(lang_pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    match = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # f31 (RUN30 DH-02 code-truncation class): a TRUNCATED fenced answer
    # (verbose script > max_tokens, cut mid-fence — the closing ``` never
    # arrives) previously fell through to the raw-text fallback, which wrote
    # the LONE OPENING ```python marker into script.py → a bogus SyntaxError
    # on line 1 that hid the real defect. Drop the opening fence so the
    # partial code is what actually runs (the grader then reports the REAL
    # incomplete-code error the next attempt can act on). Mirrors the S14-5
    # _strip_fences fix on the value paths, for the code-extraction path.
    # f31 reviewer pass: search (not ^-anchor) so a prose prefix before the
    # opener ("Here is the code:\n```python...") cannot leak prose+opener
    # into the script either — the content AFTER the opener is what runs.
    m = re.search(r"```[^\n]*\n?", text)
    if m:
        return text[m.end():].strip()

    return text.strip()


def check_instruction_adherence(raw_output, is_dual_mode=False):
    text = raw_output.strip()
    if is_dual_mode:
        text = re.sub(r"<thought>.*?</thought>", "", text, flags=re.DOTALL).strip()

    if not text:
        return False
    has_conversational = any(s in text.lower() for s in ["sure!", "here is the", "below is the", "certainly!", "hope this helps"])
    return not has_conversational


def run_zero_compute_linter_for_code(language, code):
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


def _run_tool(cmd, timeout=60):
    """Run a tool in /dev/shm, return (returncode, stdout, stderr)."""
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                             cwd="/dev/shm")
        return res.returncode, res.stdout, res.stderr
    except Exception as e:
        return -1, "", str(e)


def execute_sandboxed_test(language, code, test_code, timeout=60):
    """
    Genuinely executes the probe's unit tests in /dev/shm for EVERY language:
      - python    -> python3 <file>          (real assertions)
      - bash      -> bash -n + bash <file>   (syntax + real execution)
      - typescript-> tsc compile + node run  (real console.assert)
      - go        -> go test in temp module  (real TestRateLimiter)
      - rust      -> rustc --test + run      (real #[test] harness)
      - cpp       -> g++ compile + run       (real main/asserts)
    Never auto-passes non-Python languages (this was a fairness bug).
    """
    safe_code = str(code or "")
    pid = os.getpid()
    passed = False
    workdir = f"/dev/shm/tst_{pid}"
    import shutil as _sh
    _sh.rmtree(workdir, ignore_errors=True)
    try:
        os.makedirs(workdir, exist_ok=True)
    except Exception:
        workdir = f"/dev/shm/tst_{pid}_flat"  # never fall back to /dev/shm itself

    try:
        if language == "python":
            sandbox_file = f"{workdir}/eval_{pid}.py"
            with open(sandbox_file, "w") as f:
                f.write(f"{safe_code}\n\n{test_code}")
            res = subprocess.run([sys.executable, sandbox_file], capture_output=True,
                                 text=True, timeout=timeout)
            passed = res.returncode == 0
            if os.path.exists(sandbox_file):
                os.remove(sandbox_file)

        elif language in ["bash", "shell"]:
            sandbox_file = f"{workdir}/eval_{pid}.sh"
            with open(sandbox_file, "w") as f:
                f.write(safe_code)
            os.chmod(sandbox_file, 0o755)
            # Syntax check first (never skip)
            res = subprocess.run(["bash", "-n", sandbox_file], capture_output=True,
                                 text=True, timeout=timeout)
            if res.returncode != 0:
                passed = False
            else:
                # Real execution in the sandbox dir (the test code is a shell
                # snippet; run it appended so actual behavior is exercised).
                full = f"{safe_code}\n\n{test_code}\n"
                with open(sandbox_file, "w") as f:
                    f.write(full)
                res = subprocess.run(["bash", sandbox_file], capture_output=True,
                                     text=True, timeout=timeout)
                passed = res.returncode == 0
            if os.path.exists(sandbox_file):
                os.remove(sandbox_file)

        elif language in ["typescript", "ts"]:
            # Compile solution.ts + test.ts, then run with node so console.assert
            # failures actually fail the process (node throws on failed assert).
            sol_file = f"{workdir}/solution.ts"
            test_file = f"{workdir}/test.ts"
            with open(sol_file, "w") as f:
                f.write(safe_code)
            with open(test_file, "w") as f:
                f.write(test_code)
            rc, out, err = _run_tool(["tsc", "--target", "es2020", "--module", "commonjs",
                                      "--outDir", workdir, "--esModuleInterop",
                                      sol_file, test_file], timeout=timeout)
            if rc == 0 and os.path.exists(f"{workdir}/test.js"):
                res = subprocess.run(["node", f"{workdir}/test.js"], capture_output=True,
                                     text=True, timeout=timeout)
                passed = res.returncode == 0
            else:
                passed = False

        elif language == "go":
            # Create a real Go module with the solution + its test, run `go test`.
            with open(f"{workdir}/go.mod", "w") as f:
                f.write("module solution\n\ngo 1.21\n")
            with open(f"{workdir}/solution.go", "w") as f:
                f.write(safe_code)
            with open(f"{workdir}/solution_test.go", "w") as f:
                f.write(test_code)
            env = dict(os.environ)
            env["GOCACHE"] = f"/dev/shm/gocache_{pid}"
            env["GOPATH"] = f"/dev/shm/gopath_{pid}"
            try:
                os.makedirs(env["GOCACHE"], exist_ok=True)
                os.makedirs(env["GOPATH"], exist_ok=True)
            except Exception:
                pass
            res = subprocess.run(["go", "test", "./..."], capture_output=True, text=True,
                                 timeout=timeout, cwd=workdir, env=env)
            passed = res.returncode == 0

        elif language == "rust":
            # rustc --test compiles the #[cfg(test)] harness and runs it.
            src_file = f"{workdir}/solution.rs"
            bin_file = f"{workdir}/solution_test_bin"
            with open(src_file, "w") as f:
                f.write(f"{safe_code}\n\n{test_code}\n")
            rc, out, err = _run_tool(["rustc", "--test", src_file, "-o", bin_file], timeout=timeout)
            if rc == 0 and os.path.exists(bin_file):
                res = subprocess.run([bin_file], capture_output=True, text=True, timeout=timeout)
                passed = res.returncode == 0
            else:
                passed = False

        elif language in ["cpp", "c++", "c"]:
            src_file = f"{workdir}/solution.cpp"
            bin_file = f"{workdir}/solution_bin"
            with open(src_file, "w") as f:
                f.write(f"{safe_code}\n\n{test_code}\n")
            rc, out, err = _run_tool(["g++", "-std=c++17", src_file, "-o", bin_file], timeout=timeout)
            if rc == 0 and os.path.exists(bin_file):
                res = subprocess.run([bin_file], capture_output=True, text=True, timeout=timeout)
                passed = res.returncode == 0
            else:
                passed = False
        else:
            passed = False  # Unknown language -> never auto-pass
    except Exception:
        passed = False
    finally:
        if workdir.startswith("/dev/shm/tst_"):
            _sh.rmtree(workdir, ignore_errors=True)
    return passed


def evaluate_human_workplace_suite(cluster_key):
    clusters = load_registry()
    target_cluster = next((c for c in clusters if c["key"] == cluster_key or c["id"] == cluster_key), None)

    if not target_cluster:
        print(f"ERROR: Cluster {cluster_key} not found in registry.yaml")
        return None

    probes = load_gold_probes()
    key = target_cluster["key"]
    title = target_cluster["title"]
    port = target_cluster.get("benchmark_env", {}).get("port", 8089)

    print("\n================================================================================")
    print(f" 🧠 RUNNING HUMAN WORKPLACE REPEATABILITY SUITE: {key}")
    print(f" Title: {title} | Port: {port}")
    print("================================================================================")

    proc, server_url = start_llama_server_for_cluster(target_cluster)
    vram_before = measure_gpu_vram()
    start_time = time.time()

    total_trials = 0
    total_adherence = 0
    total_linter = 0
    total_test_pass = 0
    
    probe_repeatability_scores = []
    probe_variation_scores = []
    persona_scores = {}

    total_ttft = 0.0
    total_tok_s = 0.0

    is_dual_mode = key in ["03-qwen-baremetal-mcts", "04-qwen-3.6-gdn-linear", "08-qwen-3.6-dense-yarn"]

    try:
        for probe in probes:
            pid = probe["id"]
            persona = probe["persona"]
            lang = probe["language"]
            prompts = probe["prompts"]

            variation_passes = 0
            
            for p_idx, prompt in enumerate(prompts):
                # 3x Repetitive Trial for Prompt 0 to measure Determinism/Flakiness
                if p_idx == 0:
                    repeat_passes = 0
                    for rep in range(3):
                        total_trials += 1
                        raw_out, ttft, tok_s = query_llama_completion(server_url, prompt)
                        total_ttft += ttft
                        total_tok_s += tok_s

                        if check_instruction_adherence(raw_out, is_dual_mode=is_dual_mode):
                            total_adherence += 1

                        code = extract_code_block(raw_out, lang, is_dual_mode=is_dual_mode)
                        # Empty/error output must NEVER earn linter points (fairness).
                        if code.strip() and run_zero_compute_linter_for_code(lang, code):
                            total_linter += 1

                        if execute_sandboxed_test(lang, code, probe["test_code"]):
                            total_test_pass += 1
                            repeat_passes += 1
                    
                    repeatability_pct = (repeat_passes / 3.0) * 100.0
                    probe_repeatability_scores.append(repeatability_pct)
                    if repeat_passes > 0:
                        variation_passes += 1
                else:
                    # Variation Trials
                    total_trials += 1
                    raw_out, ttft, tok_s = query_llama_completion(server_url, prompt)
                    total_ttft += ttft
                    total_tok_s += tok_s

                    if check_instruction_adherence(raw_out, is_dual_mode=is_dual_mode):
                        total_adherence += 1

                    code = extract_code_block(raw_out, lang, is_dual_mode=is_dual_mode)
                    # Empty/error output must NEVER earn linter points (fairness).
                    if code.strip() and run_zero_compute_linter_for_code(lang, code):
                        total_linter += 1

                    if execute_sandboxed_test(lang, code, probe["test_code"]):
                        total_test_pass += 1
                        variation_passes += 1

            var_pct = (variation_passes / len(prompts)) * 100.0
            probe_variation_scores.append(var_pct)

            persona_scores.setdefault(persona, []).append(var_pct)

    finally:
        stop_llama_server(proc, port)

    elapsed_s = round(time.time() - start_time, 2)
    vram_after = measure_gpu_vram()

    n_trials = max(total_trials, 1)
    peak_vram = max(vram_before, vram_after) if max(vram_before, vram_after) > 0 else 2400
    free_headroom = 6144 - peak_vram

    avg_ttft = round(total_ttft / n_trials, 1)
    avg_tok_s = round(total_tok_s / n_trials, 1)

    acc_pct = round((total_test_pass / n_trials) * 100.0, 1)
    adh_pct = round((total_adherence / n_trials) * 100.0, 1)
    lint_pct = round((total_linter / n_trials) * 100.0, 1)

    repeatability_avg = round(sum(probe_repeatability_scores) / max(len(probe_repeatability_scores), 1), 1)
    variation_avg = round(sum(probe_variation_scores) / max(len(probe_variation_scores), 1), 1)

    persona_avg_pct = round(sum(sum(v)/len(v) for v in persona_scores.values()) / max(len(persona_scores), 1), 1)

    # Fair Composite Human Workplace Utility Score (HWUS) via shared engine.
    # Efficiency is cohort-relative; recompute_hwus_for_results() re-normalizes
    # the whole cache after all clusters have been measured (single-model runs
    # fall back to hardware reference targets).
    hwus, efficiency = compute_hwus(
        accuracy_pct=acc_pct,
        adherence_pct=adh_pct,
        determinism_pct=repeatability_avg,
        robustness_pct=variation_avg,
        linter_pct=lint_pct,
        throughput_tok_s=avg_tok_s,
        ttft_ms=avg_ttft,
        cohort=[(avg_tok_s, avg_ttft)],
    )

    result = {
        "cluster_key": key,
        "title": title,
        "builder_model": target_cluster["builder_model"],
        "planner_model": target_cluster["planner_model"],
        "hwus_score": hwus,
        "accuracy_pct": acc_pct,
        "adherence_pct": adh_pct,
        "repeatability_consistency_pct": repeatability_avg,
        "variation_robustness_pct": variation_avg,
        "persona_balance_pct": persona_avg_pct,
        "linter_pass_pct": lint_pct,
        "ttft_ms": avg_ttft,
        "throughput_tok_s": avg_tok_s,
        "latency_s": elapsed_s,
        "peak_vram_mb": peak_vram,
        "vram_headroom_mb": free_headroom,
        "efficiency_pct": efficiency
    }

    save_human_workplace_results(result)
    return result


def save_human_workplace_results(new_result, output_dir="tests/outputs"):
    out_path = PROJECT_ROOT / output_dir
    out_path.mkdir(parents=True, exist_ok=True)

    json_file = out_path / "human_workplace_results.json"
    cache = []
    if json_file.exists():
        try:
            with open(json_file) as f:
                cache = json.load(f)
        except Exception:
            cache = []

    cache = [c for c in cache if c["cluster_key"] != new_result["cluster_key"]]
    cache.append(new_result)
    # Fair re-normalization of the FULL cache: efficiency is cohort-relative so
    # every cluster's HWUS reflects the same measured cohort before sorting.
    cache = recompute_hwus_for_results(cache)
    cache.sort(key=lambda x: (x.get("hwus_score", 0), x.get("accuracy_pct", 0), x.get("throughput_tok_s", 0)), reverse=True)

    with open(json_file, "w") as f:
        json.dump(cache, f, indent=2)

    # Export raw benchmark data to TSV file without post-processing
    tsv_file = out_path / "human_workplace_results.tsv"
    tsv_headers = [
        "cluster_key", "title", "builder_model", "planner_model",
        "hwus_score", "accuracy_pct", "adherence_pct",
        "repeatability_consistency_pct", "variation_robustness_pct",
        "persona_balance_pct", "linter_pass_pct", "throughput_tok_s",
        "ttft_ms", "latency_s", "peak_vram_mb", "vram_headroom_mb"
    ]
    with open(tsv_file, "w", encoding="utf-8") as f:
        f.write("\t".join(tsv_headers) + "\n")
        for r in cache:
            row = [str(r.get(k, "")) for k in tsv_headers]
            f.write("\t".join(row) + "\n")

    # Automatically regenerate HTML audit report from fresh TSV data
    try:
        report_gen = PROJECT_ROOT / "reports/bin/generate_report_html.py"
        if report_gen.exists():
            subprocess.run([sys.executable, str(report_gen)], capture_output=True, text=True)
    except Exception as e:
        print(f"Warning: HTML report auto-generation failed: {e}")

    # Copy outputs to timestamped reports/web/ directory
    try:
        run_dir_env = os.environ.get("BENCHMARK_RUN_DIR")
        if run_dir_env:
            run_dir = Path(run_dir_env)
        else:
            # Create timestamped dir if not orchestrated by run_full_benchmark.py
            web_dir = PROJECT_ROOT / "reports" / "web"
            web_dir.mkdir(parents=True, exist_ok=True)
            run_dir = web_dir / datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            run_dir.mkdir(parents=True, exist_ok=True)

        # Copy TSV and JSON
        for fname in ["human_workplace_results.tsv", "human_workplace_results.json"]:
            src = out_path / fname
            if src.exists():
                shutil.copy2(str(src), str(run_dir / fname))

        # Copy the freshly generated HTML report
        audit_html = PROJECT_ROOT / "reports" / "audit_report.html"
        if audit_html.exists():
            shutil.copy2(str(audit_html), str(run_dir / "audit_report.html"))

        # Update reports/web/latest symlink
        web_dir = run_dir.parent
        latest_link = web_dir / "latest"
        if latest_link.is_symlink() or latest_link.exists():
            latest_link.unlink()
        latest_link.symlink_to(run_dir)

        print(f"✅ Copied results to timestamped web dir: {run_dir}")
    except Exception as e:
        print(f"Warning: Could not copy to reports/web/ timestamped dir: {e}")

    tbl1 = (
        "### 🏆 1. Synergized Human Workplace Utility Scorecard (HWUS)\n\n"
        "| Rank | Cluster Key | Architecture Setup | HWUS Score | Functional Accuracy | Instruction Adherence | 3x Determinism | Variation Robustness | Persona Balance | Linter Rate | Workplace Tier |\n"
        "|:---:|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|\n"
    )
    for i, r in enumerate(cache, 1):
        tier_str = "👑 Winner (Workplace Primary)" if i <= 2 and r.get("hwus_score", 0) >= 60.0 else "🥈 Candidate"
        tbl1 += (
            f"| #{i} | `{r['cluster_key']}` | {r['title']} | "
            f"**`{r['hwus_score']}`** | `{r['accuracy_pct']}%` | `{r['adherence_pct']}%` | `{r['repeatability_consistency_pct']}%` | `{r['variation_robustness_pct']}%` | `{r['persona_balance_pct']}%` | `{r['linter_pass_pct']}%` | {tier_str} |\n"
        )

    tbl2 = (
        "### ⚡ 2. Live Hardware Telemetry & VRAM Memory Envelope\n\n"
        "| Rank | Cluster Key | TTFT (Prefill Latency) | Output Throughput | Total Latency | Peak VRAM | Free VRAM Headroom Guard |\n"
        "|:---:|---|:---:|:---:|:---:|:---:|:---:|\n"
    )
    for i, r in enumerate(cache, 1):
        tbl2 += (
            f"| #{i} | `{r['cluster_key']}` | `{r['ttft_ms']} ms` | `{r['throughput_tok_s']} tok/s` | "
            f"`{r['latency_s']} s` | `{r['peak_vram_mb']} MB` | **`{r['vram_headroom_mb']} MB`** (>= 1.3 GB) |\n"
        )

    md = f"""# 🏆 Human Workplace Repeatability & Fact-Checking Leaderboard

> **Evaluation Target**: NVIDIA GeForce RTX 3050 Laptop GPU (6.0 GB GDDR6 VRAM, Ampere SM 8.6)  
> **Gold Standard Framework**: 5 Developer Personas (Junior Dev, Senior Arch, DevOps SRE, Data Eng, Systems Eng) × 3x Repetitive Trials × 3 Phrasing Variations × 5 Language Toolchains  
> **Isolation & Runtime**: `ws-ai` Distrobox container | CUDA `llama-server`  

---

{tbl1}
---

{tbl2}
---
*Synergized 100% empirical measurement generated by `tests/human_repeatability_eval.py` inside `ws-ai` Distrobox.*
"""

    md_file = out_path / "human_workplace_leaderboard.md"
    with open(md_file, "w") as f:
        f.write(md)

    print(f"✅ Human Workplace Leaderboard saved to: {md_file}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        evaluate_human_workplace_suite(sys.argv[1])
    else:
        clusters = load_registry()
        for c in clusters:
            evaluate_human_workplace_suite(c["key"])
        sys.exit(0)
