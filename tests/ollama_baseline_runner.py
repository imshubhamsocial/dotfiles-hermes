#!/usr/bin/env python3
"""
Ollama Aider Plan→Build Benchmark Engine
========================================
Evaluates LLM models using the SAME real developer workflow the cluster
harnesses emulate: **Aider architect (plan → build) mode** served by Ollama.

Instead of a raw `ollama run <model> <prompt>` that only ever emits a chat
response, every probe prompt is sent through Aider's architect pipeline:

    aider --architect --weak-model ollama_chat/<PLAN_MODEL> \
          --model ollama_chat/<BUILD_MODEL> --auto-accept-architect \
          --yes-always --no-git --no-auto-commits --no-analytics \
          --no-check-update --light-mode --message "<prompt>" <solution_file>

Aider routes the raw prompt to the PLAN model (architect), which thinks about
the change; the plan + repo context is then handed to the BUILD model which
applies the actual code edit to a real file. Ollama gracefully unloads the
plan model and loads the build model between the two phases — exactly the
production workflow a developer uses, so this is a proper 1:1 benchmark
against the 8 cluster harnesses (no inflated raw-emission numbers).

Methodology is IDENTICAL to the cluster suite:
- 5 developer personas × 3x repetitive trials of prompt[0] (Determinism)
- 5 developer personas × phrasing variations of prompts[1:2] (Robustness)
- Functional accuracy via sandboxed unit-test assertions in /dev/shm
- Instruction adherence (the produced file must be real code, no refusal)
- Zero-compute host linter fact-checking (ruff / biome / shellcheck / go / rustc / g++)
- Live hardware telemetry (wall latency, end-to-end throughput, peak VRAM)

ALL plan×build combinations of the 3 unique base models are benchmarked
(3 × 3 = 9 combos), so the scorecard measures every plan→build pairing.
Use `--plan <model> --build <model>` to run a single combo (dummy data), or
`--quick` to run a reduced trial set for smoke-testing.

Composite Human Workplace Utility Score (HWUS) — same fair formula as clusters,
computed by the shared engine in bin/hwus_scoring.py:
  HWUS = 0.30*Accuracy + 0.20*Adherence + 0.15*Determinism + 0.10*Robustness
       + 0.10*Linter + 0.15*Efficiency (cohort-relative, measured)
Persona balance is reported but excluded (derived from the same variation data).

Generates:
- tests/outputs/ollama_baseline_results.json
- tests/outputs/ollama_baseline_results.tsv
"""

import json
import os
import re
import shutil
import sys
import time
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from bin.c01_context_sieve_harness import run_zero_compute_linter
from bin.container_cmd import get_distrobox_cmd
from bin.hwus_scoring import compute_hwus, recompute_hwus_for_results

TOTAL_VRAM_MB = 6144  # RTX 3050 6GB envelope

# Shared native-first container resolution (see bin/container_cmd.py):
# distrobox IS natively installed at /usr/bin/distrobox on the host; the
# flatpak-spawn form is only a sandbox->host bridge used by agent shells.
DISTROBOX_CMD = get_distrobox_cmd()

# Unique Ollama models currently benchmarked (same GGUFs the clusters serve).
UNIQUE_MODELS = [
    "gemma4-qat-builder:latest",
    "qwen2.5-coder:3b",
    "qwen3.8-4b:latest",
]

MODEL_BASE_FILE = {
    "gemma4-qat-builder:latest": "gemma4-qat-builder.gguf",
    "qwen2.5-coder:3b": "qwen2.5-coder-3b-instruct-q4_k_m.gguf",
    "qwen3.8-4b:latest": "Qwen3.8-4B-Q4_K_M.gguf",
}

MODEL_TITLE = {
    "gemma4-qat-builder:latest": "Gemma 4 Base QAT INT4",
    "qwen2.5-coder:3b": "Qwen 2.5-Coder 3B Instruct Q4_K_M",
    "qwen3.8-4b:latest": "Qwen 3.8 4B Q4_K_M",
}

# 3×3 plan→build matrix (the user-requested "all combinations").
PLAN_BUILD_COMBOS = [(p, b) for p in UNIQUE_MODELS for b in UNIQUE_MODELS]


def load_gold_probes(probes_path="tests/probes/human_workplace_gold_standard.json"):
    full_path = PROJECT_ROOT / probes_path
    if not full_path.exists():
        print(f"ERROR: Gold standard probes file {full_path} not found.", flush=True)
        sys.exit(1)

    with open(full_path) as f:
        return json.load(f)


def measure_gpu_vram():
    """Returns current GPU VRAM used in MB (0 if unavailable)."""
    for cmd_args in [
        ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
        DISTROBOX_CMD + ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
    ]:
        try:
            res = subprocess.run(cmd_args, capture_output=True, text=True, timeout=3)
            if res.returncode == 0 and res.stdout.strip().isdigit():
                return int(res.stdout.strip())
        except Exception:
            pass
    return 0


EXT_MAP = {
    "python": ".py",
    "typescript": ".ts",
    "go": ".go",
    "rust": ".rs",
    "cpp": ".cpp",
    "bash": ".sh",
    "shell": ".sh",
}


def run_aider_plan_build(plan_model, build_model, prompt, language, timeout=600):
    """
    Executes ONE aider architect (plan→build) session against a fresh solution
    file. Aider's plan model receives the raw prompt; the build model applies
    the edit to the file. Returns (code, ttft_ms, tok_s, latency_s).

    Timing is measured end-to-end (process wall clock): this is the genuine
    latency a developer experiences (plan load → plan → build load → build),
    which is exactly the "engine" cost the cluster harnesses also measure.
    """
    pid = os.getpid()
    workdir = PROJECT_ROOT / f".aider_bench_tmp_{pid}"
    try:
        workdir.mkdir(parents=True, exist_ok=True)
    except Exception:
        workdir = PROJECT_ROOT / ".aider_bench_tmp"

    ext = EXT_MAP.get(str(language).lower(), ".py")
    sol_file = workdir / f"solution{ext}"
    sol_file.write_text("")  # empty target file for aider to edit

    cmd = DISTROBOX_CMD + [
        "aider",
        "--architect",
        "--weak-model", f"ollama_chat/{plan_model}",
        "--model", f"ollama_chat/{build_model}",
        "--auto-accept-architect",
        "--yes-always", "--no-git", "--no-auto-commits",
        "--no-analytics", "--no-check-update", "--light-mode",
        "--message", prompt,
        str(sol_file),
    ]

    t0 = time.time()
    first_line_ts = None
    out_lines = []
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(workdir),
        )
        for line in proc.stdout:
            if first_line_ts is None and line.strip():
                first_line_ts = time.time() - t0
            out_lines.append(line)
        try:
            proc.wait(timeout=timeout)
        except Exception:
            # Never leave an orphaned aider session running.
            try:
                proc.kill()
            except Exception:
                pass
    except Exception as e:
        print(f"⚠️ Aider error for {plan_model}→{build_model}: {e}", flush=True)
        try:
            proc.kill()
        except Exception:
            pass
    elapsed = time.time() - t0
    out = "".join(out_lines)

    code = ""
    if sol_file.exists():
        code = sol_file.read_text()

    # Parse aider's token accounting ("Tokens: 764 sent, 48 received.")
    received = 0
    m = re.search(r"Tokens:\s*(\d+)\s+sent,\s*(\d+)\s+received", out)
    if m:
        received = int(m.group(2))
    if received <= 0:
        received = max(len(re.split(r"\s+", code.strip())), 0)

    tok_s = round(received / max(elapsed, 0.001), 1) if received > 0 else 0.0
    ttft_ms = round((first_line_ts or elapsed) * 1000.0, 1)

    # Best-effort cleanup of the transient RAM/scratch dir.
    try:
        import shutil as _sh
        _sh.rmtree(workdir, ignore_errors=True)
    except Exception:
        pass

    return code, ttft_ms, tok_s, elapsed


REFUSAL_MARKERS = [
    "i can't", "i cannot", "i'm sorry", "i am sorry", "cannot help",
    "can't help", "not able to", "as an ai", "unable to",
]


def check_instruction_adherence(code_text):
    """
    Aider writes clean code into the solution file, so adherence here means:
    the build model actually produced a real, non-trivial edit (not an empty
    file, and not a conversational refusal dumped into the file).
    """
    text = str(code_text or "").strip()
    if not text:
        return False
    lowered = text.lower()
    if any(marker in lowered for marker in REFUSAL_MARKERS):
        return False
    # Must contain at least one line that looks like code, not prose.
    codey = sum(1 for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith(("#", "//", "/*", "*", "--")))
    return codey >= 1


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
    tmp_path = f"/dev/shm/sandbox_ollama_{pid}{ext}"
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
    Genuinely executes the probe's unit tests in /dev/shm for EVERY language
    (mirrors tests/human_repeatability_eval.py). Never auto-passes non-Python
    languages — that was a fairness bug that inflated functional accuracy.
    """
    safe_code = str(code or "")
    pid = os.getpid()
    passed = False
    import shutil as _sh
    workdir = f"/dev/shm/tst_ollama_{pid}"
    _sh.rmtree(workdir, ignore_errors=True)
    try:
        os.makedirs(workdir, exist_ok=True)
    except Exception:
        workdir = "/dev/shm/tst_ollama_{pid}_flat"  # never fall back to /dev/shm itself

    try:
        if language == "python":
            sandbox_file = f"{workdir}/eval_{pid}.py"
            with open(sandbox_file, "w") as f:
                f.write(f"{safe_code}\n\n{test_code}")
            try:
                res = subprocess.run([sys.executable, sandbox_file], capture_output=True,
                                     text=True, timeout=timeout)
                passed = res.returncode == 0
            except Exception:
                passed = False

        elif language in ["bash", "shell"]:
            sandbox_file = f"{workdir}/eval_{pid}.sh"
            with open(sandbox_file, "w") as f:
                f.write(safe_code)
            os.chmod(sandbox_file, 0o755)
            try:
                res = subprocess.run(["bash", "-n", sandbox_file], capture_output=True,
                                     text=True, timeout=timeout)
                if res.returncode == 0:
                    full = f"{safe_code}\n\n{test_code}\n"
                    with open(sandbox_file, "w") as f:
                        f.write(full)
                    res = subprocess.run(["bash", sandbox_file], capture_output=True,
                                         text=True, timeout=timeout)
                    passed = res.returncode == 0
            except Exception:
                passed = False

        elif language in ["typescript", "ts"]:
            sol_file = f"{workdir}/solution.ts"
            test_file = f"{workdir}/test.ts"
            with open(sol_file, "w") as f:
                f.write(safe_code)
            with open(test_file, "w") as f:
                f.write(test_code)
            try:
                rc, out, err = _run_tool(["tsc", "--target", "es2020", "--module", "commonjs",
                                          "--outDir", workdir, "--esModuleInterop",
                                          sol_file, test_file], timeout=timeout)
                if rc == 0 and os.path.exists(f"{workdir}/test.js"):
                    res = subprocess.run(["node", f"{workdir}/test.js"], capture_output=True,
                                         text=True, timeout=timeout)
                    passed = res.returncode == 0
            except Exception:
                passed = False

        elif language == "go":
            try:
                with open(f"{workdir}/go.mod", "w") as f:
                    f.write("module solution\n\ngo 1.21\n")
                with open(f"{workdir}/solution.go", "w") as f:
                    f.write(safe_code)
                with open(f"{workdir}/solution_test.go", "w") as f:
                    f.write(test_code)
                env = dict(os.environ)
                env["GOCACHE"] = f"/dev/shm/gocache_o_{pid}"
                env["GOPATH"] = f"/dev/shm/gopath_o_{pid}"
                try:
                    os.makedirs(env["GOCACHE"], exist_ok=True)
                    os.makedirs(env["GOPATH"], exist_ok=True)
                except Exception:
                    pass
                res = subprocess.run(["go", "test", "./..."], capture_output=True, text=True,
                                     timeout=timeout, cwd=workdir, env=env)
                passed = res.returncode == 0
            except Exception:
                passed = False

        elif language == "rust":
            try:
                src_file = f"{workdir}/solution.rs"
                bin_file = f"{workdir}/solution_test_bin"
                with open(src_file, "w") as f:
                    f.write(f"{safe_code}\n\n{test_code}\n")
                rc, out, err = _run_tool(["rustc", "--test", src_file, "-o", bin_file], timeout=timeout)
                if rc == 0 and os.path.exists(bin_file):
                    res = subprocess.run([bin_file], capture_output=True, text=True, timeout=timeout)
                    passed = res.returncode == 0
            except Exception:
                passed = False

        elif language in ["cpp", "c++", "c"]:
            try:
                src_file = f"{workdir}/solution.cpp"
                bin_file = f"{workdir}/solution_bin"
                with open(src_file, "w") as f:
                    f.write(f"{safe_code}\n\n{test_code}\n")
                rc, out, err = _run_tool(["g++", "-std=c++17", src_file, "-o", bin_file], timeout=timeout)
                if rc == 0 and os.path.exists(bin_file):
                    res = subprocess.run([bin_file], capture_output=True, text=True, timeout=timeout)
                    passed = res.returncode == 0
            except Exception:
                passed = False
        else:
            passed = False  # Unknown language -> never auto-pass
    except Exception:
        passed = False
    finally:
        if workdir.startswith("/dev/shm/tst_ollama_"):
            _sh.rmtree(workdir, ignore_errors=True)
    return passed


def run_ollama_combo_benchmark(plan_model, build_model, quick=False):
    """
    Runs the FULL 5-Persona × (3x repeats + 2 variations) suite — identical to
    `evaluate_human_workplace_suite` in tests/human_repeatability_eval.py —
    against one plan→build combo. With quick=True runs a reduced 1-repeat-only
    trial set (for smoke-testing / dummy data).
    """
    probes = load_gold_probes()

    combo_label = f"{plan_model} → {build_model}"
    print(f" 🤖 Evaluating Ollama Aider combo: {combo_label}{' (QUICK)' if quick else ''}...", flush=True)

    total_trials = 0
    total_adherence = 0
    total_linter = 0
    total_test_pass = 0

    probe_repeatability_scores = []
    probe_variation_scores = []
    persona_scores = {}

    total_ttft = 0.0
    total_tok_s = 0.0
    total_latency = 0.0

    peak_vram = 0
    start_time = time.time()

    for probe in probes:
        persona = probe["persona"]
        lang = probe["language"]
        prompts = probe["prompts"]

        variation_passes = 0
        repeat_passes = 0

        for p_idx, prompt in enumerate(prompts):
            if quick:
                # Reduced smoke-test set: only prompt[0] once per probe.
                if p_idx != 0:
                    continue
                total_trials += 1
                code, ttft, tok_s, lat = run_aider_plan_build(plan_model, build_model, prompt, lang)
                total_ttft += ttft
                total_tok_s += tok_s
                total_latency += lat
                if check_instruction_adherence(code):
                    total_adherence += 1
                # Empty/error output must NEVER earn linter points (fairness).
                if code.strip() and run_zero_compute_linter_for_code(lang, code):
                    total_linter += 1
                if execute_sandboxed_test(lang, code, probe["test_code"]):
                    total_test_pass += 1
                    repeat_passes += 1
                    variation_passes += 1
                probe_repeatability_scores.append(100.0 if repeat_passes > 0 else 0.0)
                continue

            # 3x Repetitive Trial for Prompt 0 to measure Determinism/Flakiness
            if p_idx == 0:
                rep_passes = 0
                for rep in range(3):
                    total_trials += 1
                    code, ttft, tok_s, lat = run_aider_plan_build(plan_model, build_model, prompt, lang)
                    total_ttft += ttft
                    total_tok_s += tok_s
                    total_latency += lat

                    if check_instruction_adherence(code):
                        total_adherence += 1

                    # Empty/error output must NEVER earn linter points (fairness).
                    if code.strip() and run_zero_compute_linter_for_code(lang, code):
                        total_linter += 1

                    if execute_sandboxed_test(lang, code, probe["test_code"]):
                        total_test_pass += 1
                        rep_passes += 1

                repeatability_pct = (rep_passes / 3.0) * 100.0
                probe_repeatability_scores.append(repeatability_pct)
                if rep_passes > 0:
                    variation_passes += 1
            else:
                # Variation Trials
                total_trials += 1
                code, ttft, tok_s, lat = run_aider_plan_build(plan_model, build_model, prompt, lang)
                total_ttft += ttft
                total_tok_s += tok_s
                total_latency += lat

                if check_instruction_adherence(code):
                    total_adherence += 1

                # Empty/error output must NEVER earn linter points (fairness).
                if code.strip() and run_zero_compute_linter_for_code(lang, code):
                    total_linter += 1

                if execute_sandboxed_test(lang, code, probe["test_code"]):
                    total_test_pass += 1
                    variation_passes += 1

        var_pct = (variation_passes / max(len(prompts), 1)) * 100.0 if not quick else variation_passes * 100.0
        probe_variation_scores.append(var_pct)

        persona_scores.setdefault(persona, []).append(var_pct)

        vram_now = measure_gpu_vram()
        if vram_now > peak_vram:
            peak_vram = vram_now

    elapsed_s = round(time.time() - start_time, 2)

    n_trials = max(total_trials, 1)
    peak_vram = max(peak_vram, 2200)  # floor: model always resident in VRAM
    free_headroom = max(TOTAL_VRAM_MB - peak_vram, 0)

    avg_ttft = round(total_ttft / n_trials, 1)
    avg_tok_s = round(total_tok_s / n_trials, 1)
    avg_latency = round(total_latency / n_trials, 2)

    acc_pct = round((total_test_pass / n_trials) * 100.0, 1)
    adh_pct = round((total_adherence / n_trials) * 100.0, 1)
    lint_pct = round((total_linter / n_trials) * 100.0, 1)

    repeatability_avg = round(sum(probe_repeatability_scores) / max(len(probe_repeatability_scores), 1), 1)
    variation_avg = round(sum(probe_variation_scores) / max(len(probe_variation_scores), 1), 1)

    persona_avg_pct = round(sum(sum(v) / len(v) for v in persona_scores.values()) / max(len(persona_scores), 1), 1)

    # Fair Composite Human Workplace Utility Score (HWUS) — shared engine,
    # identical to the cluster harness. Efficiency is cohort-relative and gets
    # re-normalized across the full combo set in main() before saving.
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

    print(f" [HWUS: {hwus} | Acc: {acc_pct}% | Adh: {adh_pct}% | Det: {repeatability_avg}% | Rob: {variation_avg}% | Lint: {lint_pct}% | {avg_tok_s} tok/s | TTFT {avg_ttft} ms]", flush=True)

    return {
        "hwus_score": hwus,
        "accuracy_pct": acc_pct,
        "adherence_pct": adh_pct,
        "repeatability_consistency_pct": repeatability_avg,
        "variation_robustness_pct": variation_avg,
        "persona_balance_pct": persona_avg_pct,
        "linter_pass_pct": lint_pct,
        "throughput_tok_s": avg_tok_s,
        "ttft_ms": avg_ttft,
        "latency_s": avg_latency,
        "peak_vram_mb": peak_vram,
        "vram_headroom_mb": free_headroom,
        "efficiency_pct": efficiency
    }


def main():
    out_dir = PROJECT_ROOT / "tests/outputs"
    out_dir.mkdir(parents=True, exist_ok=True)

    # CLI: run a single plan→build combo (--plan X --build Y) or all 9 combos.
    only_plan = None
    only_build = None
    quick = False
    args = sys.argv[1:]
    if "--plan" in args and args.index("--plan") + 1 < len(args):
        only_plan = args[args.index("--plan") + 1]
    if "--build" in args and args.index("--build") + 1 < len(args):
        only_build = args[args.index("--build") + 1]
    if "--quick" in args:
        quick = True

    combos = PLAN_BUILD_COMBOS
    if only_plan and only_build:
        combos = [(only_plan, only_build)]
    elif only_plan:
        combos = [(only_plan, b) for b in UNIQUE_MODELS]
    elif only_build:
        combos = [(p, only_build) for p in UNIQUE_MODELS]

    print(f" 🦙 Ollama Aider Plan→Build Benchmark: {len(combos)} combo(s) to evaluate.", flush=True)

    combo_results = {}
    for plan_model, build_model in combos:
        label = f"{plan_model} → {build_model}"
        combo_results[label] = run_ollama_combo_benchmark(plan_model, build_model, quick=quick)

    results = []
    for plan_model, build_model in combos:
        label = f"{plan_model} → {build_model}"
        metrics = combo_results[label]
        base = dict(metrics)
        base["cluster_key"] = f"combo-{plan_model.replace(':', '_')}--{build_model.replace(':', '_')}"
        base["ollama_model"] = f"{plan_model} → {build_model}"
        base["plan_model"] = plan_model
        base["build_model"] = build_model
        base["title"] = f"Plan: {MODEL_TITLE.get(plan_model, plan_model)} → Build: {MODEL_TITLE.get(build_model, build_model)}"
        base["base_file"] = MODEL_BASE_FILE.get(build_model, "gguf")
        results.append(base)

    # Fair re-normalization of the FULL combo cohort (efficiency is cohort-relative)
    results = recompute_hwus_for_results(results)
    results.sort(key=lambda x: x["hwus_score"], reverse=True)

    json_file = out_dir / "ollama_baseline_results.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    tsv_file = out_dir / "ollama_baseline_results.tsv"
    tsv_headers = [
        "cluster_key", "ollama_model", "plan_model", "build_model", "title", "base_file",
        "hwus_score", "accuracy_pct", "adherence_pct",
        "repeatability_consistency_pct", "variation_robustness_pct",
        "persona_balance_pct", "linter_pass_pct", "throughput_tok_s",
        "ttft_ms", "latency_s", "peak_vram_mb", "vram_headroom_mb"
    ]
    with open(tsv_file, "w", encoding="utf-8") as f:
        f.write("\t".join(tsv_headers) + "\n")
        for r in results:
            row = [str(r.get(k, "")) for k in tsv_headers]
            f.write("\t".join(row) + "\n")

    print(f"\n✅ Ollama Aider Plan→Build Benchmark completed. Saved {len(results)} entries to:")
    print(f"   JSON: {json_file}")
    print(f"   TSV : {tsv_file}", flush=True)


if __name__ == "__main__":
    main()
