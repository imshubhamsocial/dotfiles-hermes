#!/usr/bin/env python3
"""
llama.cpp Cluster-as-Model Aider Plan→Build Benchmark Engine
==============================================================
Replaces the old Vanilla-Ollama baseline. There are NO raw base-model tests
here. Instead, each of the 8 research clusters IS a "model": its llama-server
is launched with the EXACT flags mandated by its research paper (registry.yaml
`benchmark_env` + research-mandated extras), and the plan→build workflow is
driven by Aider — the same real developer workflow the clusters emulate.

Benchmark model (one plan→build pair per run):
  Phase A (PLAN):  plan cluster's llama-server starts with its research flags.
                   Aider (in ws-ai, with its AST / QWD / MCP / reranker setup)
                   receives the raw prompt and produces a detailed plan.
                   Plan server is then gracefully unloaded.
  Phase B (BUILD): build cluster's llama-server starts with ITS research flags.
                   Aider receives the prompt + captured plan and applies a real
                   edit to a solution file. Build server is then unloaded.

This is a true 1:1 test of the SAME benchmarks the cluster harnesses use:
- 5 developer personas × 3x repetitive trials of prompt[0] (Determinism)
- 5 developer personas × phrasing variations of prompts[1:2] (Robustness)
- Functional accuracy via sandboxed unit-test assertions in /dev/shm
- Instruction adherence (the produced file must be real code, no refusal)
- Zero-compute host linter fact-checking (ruff / biome / shellcheck / go / rustc / g++)
- Live hardware telemetry (wall latency, end-to-end throughput, peak VRAM)

ALL plan×build combinations of the 8 clusters are benchmarked
(8 × 8 = 64 combos) so the scorecard measures every plan→build pairing —
self pairs (cluster N plans + same cluster N builds) give the fairest 1:1
baseline for that cluster; cross pairs reveal the best plan/build combo.
Use `--plan-cluster 01 --build-cluster 02 --quick` to run a single pair
(dummy data), or `--quick` to run a reduced trial set for smoke-testing.

Composite Human Workplace Utility Score (HWUS) — same fair formula as clusters,
computed by the shared engine in bin/hwus_scoring.py:
  HWUS = 0.30*Accuracy + 0.20*Adherence + 0.15*Determinism + 0.10*Robustness
       + 0.10*Linter + 0.15*Efficiency (cohort-relative, measured)

Generates:
- tests/outputs/llamacpp_baseline_results.json
- tests/outputs/llamacpp_baseline_results.tsv
"""

import json
import os
import re
import shutil
import sys
import time
import subprocess
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from bin.c01_context_sieve_harness import run_zero_compute_linter
from bin.container_cmd import get_distrobox_cmd
from bin.hwus_scoring import compute_hwus, recompute_hwus_for_results
from tests.ollama_baseline_runner import (
    check_instruction_adherence,
    execute_sandboxed_test,
    load_gold_probes,
    measure_gpu_vram,
    run_zero_compute_linter_for_code,
)

TOTAL_VRAM_MB = 6144  # RTX 3050 6GB envelope

DISTROBOX_CMD = get_distrobox_cmd()

LLAMA_SERVER_BIN = PROJECT_ROOT / "llama.cpp" / "build" / "bin" / "llama-server"
ASSETS_DIR = PROJECT_ROOT / "assets"

# Session-11 f24: per-config llama-server binary override. The certified build
# (llama.cpp/build/bin) stays the DEFAULT — clusters 01-08 and every experiment
# without the key launch byte-identically. An experiment may pin a DIFFERENT
# build via the top-level `server_bin` key (repo-relative path) in its config:
# e4/P4 (speculative decoding) needs the OpenSSL build
# (llama.cpp/build_openssl/bin/llama-server) because --spec-draft-hf's HF
# download requires HTTPS (the certified build compiles without OpenSSL).
def server_bin_for(cluster_cfg):
    """Resolve the llama-server binary for a cluster cfg: the config's
    `server_bin` (repo-relative) when set and on disk, else the certified
    build/bin binary. Certified clusters (no key) → LLAMA_SERVER_BIN."""
    rel = str((cluster_cfg or {}).get("server_bin") or "").strip()
    if rel:
        p = (PROJECT_ROOT / rel).resolve()
        if p.is_file():
            return p
    return LLAMA_SERVER_BIN


# CLI dialect difference between the certified build and the thecodacus fork
# (2026-08-09, e9b crash — VERIFIED LIVE): the certified build (commit e1a1abb)
# accepts `--load-mode mlock` (the new spell); the thecodacus fork (commit
# 5e7f627, the GDR Batch-A / "Claude improved llama.cpp" build) only accepts
# the legacy `--mlock` — `--load-mode` kills it instantly with
# "error: invalid argument: --load-mode" (37-byte server log, 27 unhealthy
# cells). Probed once per binary (--help grep) and cached, so a fork-pinned
# row launches with its own dialect while certified rows stay byte-identical.
_MLOCK_DIALECT_CACHE: dict[str, str] = {}


def mlock_dialect_flag(server_bin: Path) -> str:
    """'--load-mode mlock' (certified dialect) or '--mlock' (fork dialect)
    for the given resolved server binary. Probes the binary's --help once and
    caches per path; unknown binaries default to the CERTIFIED dialect so
    nothing existing changes."""
    key = str(server_bin)
    if key not in _MLOCK_DIALECT_CACHE:
        flag = "--load-mode mlock"  # certified default (e1a1abb dialect)
        try:
            lib = str(server_bin.parent)
            env = dict(os.environ)
            env["LD_LIBRARY_PATH"] = f"{lib}:" + env.get("LD_LIBRARY_PATH", "")
            help_out = subprocess.run(
                [str(server_bin), "--help"], capture_output=True, text=True,
                timeout=10, env=env).stdout
            # the fork's help lists --mlock but NOT --load-mode → use legacy
            if "--mlock" in help_out and "--load-mode" not in help_out:
                flag = "--mlock"
        except Exception:
            flag = "--load-mode mlock"  # probe failed → safe certified default
        _MLOCK_DIALECT_CACHE[key] = flag
    return _MLOCK_DIALECT_CACHE[key]


def mlock_args_for(server_bin: Path) -> list[str]:
    """The mlock argv tokens for the resolved binary's dialect."""
    return mlock_dialect_flag(server_bin).split()

# Research-mandated extra llama-server flags (beyond registry benchmark_env).
# Source: researches/*/README.md "Execution Command Recipes" + DEPLOYMENT.md.
MLOCK_CLUSTERS = {"cluster2", "cluster3", "cluster4"}          # --load-mode mlock
FLASH_ATTN_CLUSTERS = {"cluster1", "cluster2", "cluster3", "cluster4"}  # -fa on
LORA_CLUSTERS = {"cluster1", "cluster5"}                        # --lora --lora-init-without-apply


def load_registry():
    import yaml
    with open(PROJECT_ROOT / "registry.yaml") as f:
        data = yaml.safe_load(f)
    return data.get("clusters", [])


def cluster_by_id(clusters, cid):
    cid = str(cid)
    for c in clusters:
        if c["id"] == cid or c["id"].endswith(cid):
            return c
        if c["key"].split("-")[0] == cid:
            return c
    return None


def build_llama_server_cmd(cluster_cfg):
    """Build the EXACT llama-server launch args for a cluster from registry
    benchmark_env + research-mandated extras. Never deviates from research."""
    env = cluster_cfg.get("benchmark_env", {})
    port = int(env.get("port", 8089))
    ctx = int(env.get("context_length", 4096))
    ngl = int(env.get("n_gpu_layers", 99))
    np_slots = int(env.get("parallel_slots", 1))

    model_rel = cluster_cfg["builder_model"].split()[0]
    model_path = ASSETS_DIR / model_rel if not os.path.isabs(model_rel) else Path(model_rel)

    server_bin = server_bin_for(cluster_cfg)
    cmd = [
        str(server_bin),
        "-m", str(model_path),
        "-c", str(ctx),
        "--host", "127.0.0.1",
        "--port", str(port),
        "-ngl", str(ngl),
        "-np", str(np_slots),
    ]

    if cluster_cfg["id"] in FLASH_ATTN_CLUSTERS or env.get("flash_attn"):
        cmd += ["-fa", "on"]

    if env.get("cache_type_k"):
        cmd += ["--cache-type-k", env["cache_type_k"],
                "--cache-type-v", env.get("cache_type_v", "q8_0")]

    if cluster_cfg["id"] in LORA_CLUSTERS and env.get("lora_path"):
        lora_p = PROJECT_ROOT / env["lora_path"]
        cmd += ["--lora", str(lora_p), "--lora-init-without-apply"]

    if cluster_cfg["id"] in MLOCK_CLUSTERS:
        cmd += mlock_args_for(server_bin)

    # Aider talks to the server through OpenAI-compatible /chat/completions.
    # Some models (e.g. Qwen 3.6) ship a strict embedded Jinja template that
    # raises on aider's system-message ordering (HTTP 400 "System message must
    # be at the beginning"). --no-jinja uses the engine's built-in chat
    # template so every cluster accepts aider's message format identically.
    cmd += ["--no-jinja"]

    # ── Experiment config extensions (Session-11 f23 — P1-P7 probes) ──────
    # Extended benchmark_env keys read ONLY from experiments.yaml configs (the
    # certified registry clusters never set them, so the frozen research flags
    # are byte-identical):
    #   load_mode: "mlock"   → --load-mode mlock (explicit per-config, in
    #                           addition to the legacy MLOCK_CLUSTERS id set)
    #   jinja: true           → --jinja AFTER --no-jinja (last-flag-wins: gemma4
    #                           and reasoning models need the embedded template)
    #   reasoning: "on"       → --reasoning on [+ budget/format]; llama-server
    #                           routes thoughts → reasoning_content (r06 §4)
    #   draft_model: <gguf>   → --model-draft <path> (speculative decoding)
    if env.get("load_mode") == "mlock":
        cmd += mlock_args_for(server_bin)
    # 2026-08-14 (swap-abort fix — cache-ram): llama.cpp's in-memory prompt
    # cache defaults to --cache-ram 8192 (8 GiB of HOST RAM; server-context.cpp
    # params cache_ram_mib default) and stores KV states per request — with a
    # 64K ctx each entry is ~839 MiB, so long HILO sessions pushed the server's
    # VmSwap past 5.6 GiB → swap_watch HARD ABORT (3 kills in 24 h). benchmark_env
    # `cache_ram: N` (MiB; 0 = disable) bounds it — HILO rows set 0 (the server
    # re-prefills per request; ~32% reuse measured, not worth the RAM).
    if env.get("cache_ram") is not None:
        cmd += ["--cache-ram", str(env["cache_ram"])]
    if env.get("jinja"):
        cmd += ["--jinja"]
    if str(env.get("reasoning", "")).lower() == "on":
        cmd += ["--reasoning", "on"]
        if env.get("reasoning_budget"):
            cmd += ["--reasoning-budget", str(env["reasoning_budget"])]
        if env.get("reasoning_format"):
            cmd += ["--reasoning-format", str(env["reasoning_format"])]
    # GDR merged plan (2026-08-08 — e9/e9b/e13 MoE expert-offload recipe):
    #   n_cpu_moe: <int> → --n-cpu-moe <n> (pin expert weights to CPU RAM;
    #                      attention/routing stay on GPU — the 35B-video recipe)
    #   no_mmap: true     → --no-mmap (read the whole model into RAM upfront so
    #                      expert lookups never page-fault mid-token)
    if env.get("n_cpu_moe"):
        cmd += ["--n-cpu-moe", str(env["n_cpu_moe"])]
    if env.get("no_mmap"):
        cmd += ["--no-mmap"]
    # draft_model lives at the cluster TOP level (mirrors builder_model —
    # experiments.yaml convention); accepted from benchmark_env too.
    # Session-11 f24 (P4 UNBLOCKED — live-verified): this llama.cpp (commit
    # e1a1abb) DOES ship `--model-draft FNAME` (help line 366: alias of
    # --spec-draft-model/-md) — the f23 runbook claim that it was removed was
    # WRONG (a help-grep missed it). The local GGUF draft loads on the
    # CERTIFIED build (no OpenSSL needed) and the server serves health 200.
    # The HF-repo form `--spec-draft-hf <repo>:<quant>` is emitted ONLY for
    # repo strings (a 'user/model' pair: contains '/' and is not a local
    # path) — it was live-verified to resolve an EMPTY draft path on this
    # build (plan_spec resolves, tasks never populate path), so the
    # local-file path is the default for e4/P4. Local forms: bare asset name
    # (assets/<name>), absolute path (/dev/shm/…), or relative path
    # (./models/…).
    draft = str(cluster_cfg.get("draft_model") or env.get("draft_model")
                or "").strip()
    if draft:
        if os.path.isabs(draft) or "/" not in draft:
            # local GGUF: absolute path or bare asset name (assets/<name>)
            dpath = Path(draft) if os.path.isabs(draft) else ASSETS_DIR / draft
            cmd += ["--model-draft", str(dpath)]
        elif draft.startswith("."):
            # relative local path (e.g. ./models/draft.gguf)
            cmd += ["--model-draft", str(Path(draft))]
        else:
            # HF repo (user/model[:quant])
            cmd += ["--spec-draft-hf", draft]

    return cmd, port


def cleanup_port(port):
    # Kill only the llama-server bound to THIS port — never touch other
    # llama-server instances (e.g. cluster harnesses running concurrently).
    subprocess.run(["pkill", "-9", "-f", f"llama-server.*--port {port}"], capture_output=True)
    subprocess.run(["fuser", "-k", "-9", f"{port}/tcp"], capture_output=True)


def start_llama_server(cluster_cfg):
    """Start a cluster's llama-server with research flags, wait for it to serve.

    Returns (proc, port). On hard failure (model load error / crash) it logs the
    server stderr tail to tests/outputs/llamacpp_server_<id>.log and returns
    (None, port) so callers can record the trial as a genuine failure instead of
    polling a dead server.
    """
    cmd, port = build_llama_server_cmd(cluster_cfg)
    cleanup_port(port)
    time.sleep(1)

    lib_path = str(server_bin_for(cluster_cfg).parent)
    env_setup = f"export LD_LIBRARY_PATH={lib_path}:$LD_LIBRARY_PATH; "
    full_cmd = DISTROBOX_CMD + ["bash", "-lc", env_setup + " ".join(f"'{a}'" if " " in a else a for a in cmd)]

    log_dir = PROJECT_ROOT / "tests" / "outputs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"llamacpp_server_{cluster_cfg['id']}.log"
    log_fh = open(log_path, "w", encoding="utf-8")

    proc = subprocess.Popen(full_cmd, stdout=log_fh, stderr=subprocess.STDOUT, text=True)
    url = f"http://127.0.0.1:{port}/v1/models"
    for _ in range(120):
        if proc.poll() is not None:
            # Server exited before becoming healthy (e.g. CUDA OOM, bad model).
            log_fh.flush()
            log_fh.close()
            try:
                with open(log_path, "r", encoding="utf-8") as f:
                    tail = "\n".join(f.read().splitlines()[-6:])
            except Exception:
                tail = "(no log)"
            print(f"❌ llama-server for {cluster_cfg['id']} on port {port} exited early:\n{tail}", flush=True)
            return None, port
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    log_fh.close()
                    return proc, port
        except Exception:
            time.sleep(1)
    log_fh.close()
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            tail = "\n".join(f.read().splitlines()[-6:])
    except Exception:
        tail = "(no log)"
    print(f"⚠️  llama-server health check timed out for {cluster_cfg['id']} on port {port} (log: {log_path})\n{tail}", flush=True)
    return proc, port


def stop_llama_server(proc, port):
    """Graceful unload: SIGTERM first, then SIGKILL fallback, then free the port."""
    if proc:
        try:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except Exception:
                proc.kill()
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
    time.sleep(1)
    subprocess.run(["fuser", "-k", "-9", f"{port}/tcp"], capture_output=True)


def run_aider_plan(plan_cluster, prompt):
    """Phase A: plan cluster's server + aider producing a plan (no edits)."""
    proc, port = start_llama_server(plan_cluster)
    if proc is None:
        # Server failed to start (e.g. CUDA OOM) — record a genuine failure fast
        # instead of letting aider hang against a dead port.
        return ""

    api_base = f"http://127.0.0.1:{port}/v1"
    plan_prompt = (
        f"{prompt}\n\n"
        "Produce ONLY a detailed step-by-step implementation plan. "
        "Do NOT edit any files. Wrap the plan between the markers "
        "<!--PLAN_START--> and <!--PLAN_END-->."
    )
    # Aider needs a model name it has metadata for; llama-server ignores the
    # model field and serves whatever GGUF is loaded, so gpt-4o-mini is just a
    # placeholder that aider accepts with --openai-api-base pointed at llama.cpp.
    aider_cmd = DISTROBOX_CMD + [
        "aider",
        "--model", "openai/gpt-4o-mini",
        "--openai-api-base", api_base,
        "--openai-api-key", "not-needed",
        "--no-show-model-warnings",
        "--yes-always", "--no-git", "--no-auto-commits",
        "--no-analytics", "--no-check-update", "--light-mode",
        "--message", plan_prompt,
    ]

    t0 = time.time()
    try:
        res = subprocess.run(aider_cmd, capture_output=True, text=True, timeout=600, cwd=str(PROJECT_ROOT))
        out = (res.stdout or "") + (res.stderr or "")
    except Exception as e:
        out = f"AIDER PLAN ERROR: {e}"

    stop_llama_server(proc, port)

    m = re.search(r"<!--PLAN_START-->(.*?)<!--PLAN_END-->", out, re.DOTALL)
    plan = m.group(1).strip() if m else out.strip()
    if not plan:
        plan = out.strip()
    return plan


def run_aider_build(build_cluster, prompt, plan, language):
    """Phase B: build cluster's server + aider applying the plan to a solution file."""
    workdir = PROJECT_ROOT / f".llamacpp_tmp_{os.getpid()}"
    try:
        workdir.mkdir(parents=True, exist_ok=True)
    except Exception:
        workdir = PROJECT_ROOT / ".llamacpp_tmp"

    ext_map = {"python": ".py", "typescript": ".ts", "go": ".go", "rust": ".rs",
               "cpp": ".cpp", "bash": ".sh", "shell": ".sh"}
    ext = ext_map.get(str(language).lower(), ".py")
    sol_file = workdir / f"solution{ext}"
    sol_file.write_text("")

    proc, port = start_llama_server(build_cluster)
    if proc is None:
        # Server failed to start (e.g. CUDA OOM) — record a genuine failure fast.
        try:
            shutil.rmtree(workdir, ignore_errors=True)
        except Exception:
            pass
        return "", 0.0, 0.0, 0.0

    api_base = f"http://127.0.0.1:{port}/v1"
    build_prompt = f"{prompt}\n\nPLAN:\n{plan}" if plan else prompt

    # Same placeholder-model approach as the plan phase: llama-server serves
    # the build cluster's GGUF regardless of the requested model name.
    aider_cmd = DISTROBOX_CMD + [
        "aider",
        "--model", "openai/gpt-4o-mini",
        "--openai-api-base", api_base,
        "--openai-api-key", "not-needed",
        "--no-show-model-warnings",
        "--yes-always", "--no-git", "--no-auto-commits",
        "--no-analytics", "--no-check-update", "--light-mode",
        "--message", build_prompt,
        str(sol_file),
    ]

    t0 = time.time()
    first_line_ts = None
    out_lines = []
    try:
        proc_aider = subprocess.Popen(aider_cmd, stdout=subprocess.PIPE,
                                      stderr=subprocess.STDOUT, text=True,
                                      cwd=str(workdir))
        for line in proc_aider.stdout:
            if first_line_ts is None and line.strip():
                first_line_ts = time.time() - t0
            out_lines.append(line)
        try:
            proc_aider.wait(timeout=600)
        except Exception:
            try:
                proc_aider.kill()
            except Exception:
                pass
    except Exception as e:
        print(f"⚠️  Aider build error for {build_cluster['id']}: {e}", flush=True)
        try:
            proc_aider.kill()
        except Exception:
            pass
    elapsed = time.time() - t0
    out = "".join(out_lines)

    stop_llama_server(proc, port)

    code = sol_file.read_text() if sol_file.exists() else ""

    # Aider's build model may create a NEW file (e.g. path/to/filename.js)
    # instead of editing the empty placeholder — scan the workdir for any
    # produced source file and use it as the measured solution. Accept any
    # non-dotfile source created during this trial (dedicated workdir), newest
    # wins; the target extension is preferred but never required.
    if not code.strip() and workdir.exists():
        source_suffixes = {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".c", ".cpp", ".h", ".hpp", ".sh", ".bash", ".yml", ".yaml", ".json"}
        candidate = None
        best_mtime = 0.0
        for f in workdir.rglob("*"):
            if not f.is_file():
                continue
            rel = f.relative_to(workdir).as_posix()
            if rel.startswith(".") or rel in ("solution" + ext,):
                continue
            if f.suffix in source_suffixes:
                if f.stat().st_mtime > best_mtime:
                    best_mtime = f.stat().st_mtime
                    candidate = f
        if candidate:
            code = candidate.read_text(errors="replace")

    received = 0
    m = re.search(r"Tokens:\s*(\d+)\s+sent,\s*(\d+)\s+received", out)
    if m:
        received = int(m.group(2))
    if received <= 0:
        received = max(len(re.split(r"\s+", code.strip())), 0)

    tok_s = round(received / max(elapsed, 0.001), 1) if received > 0 else 0.0
    ttft_ms = round((first_line_ts or elapsed) * 1000.0, 1)

    try:
        shutil.rmtree(workdir, ignore_errors=True)
    except Exception:
        pass

    return code, ttft_ms, tok_s, elapsed


def run_combo_benchmark(plan_cluster, build_cluster, quick=False):
    """Runs the FULL 5-Persona × (3x repeats + 2 variations) suite — identical
    to tests/human_repeatability_eval.py — against one plan→build pair."""
    probes = load_gold_probes()

    def _pretty(cid):
        return str(cid).replace('cluster', '').zfill(2)

    combo_label = f"Plan: Cluster {_pretty(plan_cluster['id'])} → Build: Cluster {_pretty(build_cluster['id'])}"
    print(f" 🤖 Evaluating llama.cpp cluster combo: {combo_label}{' (QUICK)' if quick else ''}...", flush=True)

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
                plan = run_aider_plan(plan_cluster, prompt)
                code, ttft, tok_s, lat = run_aider_build(build_cluster, prompt, plan, lang)
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
                    plan = run_aider_plan(plan_cluster, prompt)
                    code, ttft, tok_s, lat = run_aider_build(build_cluster, prompt, plan, lang)
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
                plan = run_aider_plan(plan_cluster, prompt)
                code, ttft, tok_s, lat = run_aider_build(build_cluster, prompt, plan, lang)
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
    out_dir = PROJECT_ROOT / "tests" / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)

    only_plan = None
    only_build = None
    quick = False
    explicit_pairs = []  # [(plan, build)] from repeatable --pair flags
    args = sys.argv[1:]
    if "--pair" in args:
        while "--pair" in args:
            i = args.index("--pair")
            if i + 1 < len(args):
                explicit_pairs.append(args[i + 1])
                args = args[:i] + args[i + 2:]
            else:
                break
    if "--plan-cluster" in args and args.index("--plan-cluster") + 1 < len(args):
        only_plan = args[args.index("--plan-cluster") + 1]
    elif "--plan" in args and args.index("--plan") + 1 < len(args):
        only_plan = args[args.index("--plan") + 1]
    if "--build-cluster" in args and args.index("--build-cluster") + 1 < len(args):
        only_build = args[args.index("--build-cluster") + 1]
    elif "--build" in args and args.index("--build") + 1 < len(args):
        only_build = args[args.index("--build") + 1]
    if "--quick" in args:
        quick = True

    clusters = load_registry()
    if explicit_pairs:
        combos = []
        for pair in explicit_pairs:
            parts = pair.replace(",", " ").split()
            if len(parts) >= 2:
                pc = cluster_by_id(clusters, parts[0])
                bc = cluster_by_id(clusters, parts[1])
                if pc and bc:
                    combos.append((pc, bc))
    elif only_plan and only_build:
        pc = cluster_by_id(clusters, only_plan)
        bc = cluster_by_id(clusters, only_build)
        combos = [(pc, bc)] if pc and bc else []
    elif only_plan:
        pc = cluster_by_id(clusters, only_plan)
        combos = [(pc, bc) for bc in clusters if pc]
    elif only_build:
        bc = cluster_by_id(clusters, only_build)
        combos = [(pc, bc) for pc in clusters if bc]
    else:
        combos = [(p, b) for p in clusters for b in clusters]  # 8 × 8 = 64

    if not combos:
        print("ERROR: no matching clusters in registry.yaml", flush=True)
        sys.exit(1)

    print(f" 🦙 llama.cpp Cluster-as-Model Aider Plan→Build Benchmark: {len(combos)} combo(s).", flush=True)

    combo_results = {}
    for pc, bc in combos:
        label = f"{pc['id']} → {bc['id']}"
        combo_results[label] = run_combo_benchmark(pc, bc, quick=quick)

    results = []
    for pc, bc in combos:
        label = f"{pc['id']} → {bc['id']}"
        metrics = combo_results[label]
        base = dict(metrics)
        base["cluster_key"] = f"llamacpp-combo-{pc['id']}--{bc['id']}"
        base["source"] = "measured"
        def _pretty(cid):
            return str(cid).replace('cluster', '').zfill(2)
        combo_label = f"Plan: Cluster {_pretty(pc['id'])} → Build: Cluster {_pretty(bc['id'])}"
        base["llamacpp_model"] = combo_label
        base["plan_cluster"] = pc["id"]
        base["build_cluster"] = bc["id"]
        # Legacy-compatible columns so the report generator's loader keeps
        # working with zero changes: ollama_model = combo label (unique per
        # row, so dedup never collapses combos), plan/build model = cluster ids.
        base["ollama_model"] = combo_label
        base["plan_model"] = pc["id"]
        base["build_model"] = bc["id"]
        base["title"] = f"Plan: {pc['title']} → Build: {bc['title']}"
        base["base_file"] = bc["builder_model"].split()[0]
        results.append(base)

    results = recompute_hwus_for_results(results)

    # ── Merge with any previously-measured rows (same cluster_key) so a
    #    partial / incremental run (e.g. 2 smoke pairs) never clobbers the
    #    real data of earlier pairs. New rows win on duplicate keys.
    json_file = out_dir / "llamacpp_baseline_results.json"
    if json_file.exists():
        try:
            with open(json_file, encoding="utf-8") as f:
                existing = json.load(f)
            if isinstance(existing, list):
                merged = {r["cluster_key"]: r for r in existing}
                for r in results:
                    merged[r["cluster_key"]] = r
                results = list(merged.values())
        except Exception:
            pass  # unreadable/partial file → just overwrite

    results = recompute_hwus_for_results(results)
    results.sort(key=lambda x: x["hwus_score"], reverse=True)

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    tsv_file = out_dir / "llamacpp_baseline_results.tsv"
    tsv_headers = [
        "cluster_key", "llamacpp_model", "ollama_model", "plan_cluster", "build_cluster",
        "plan_model", "build_model", "title", "base_file",
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

    print(f"\n✅ llama.cpp Cluster-as-Model Benchmark completed. Saved {len(results)} entries to:")
    print(f"   JSON: {json_file}")
    print(f"   TSV : {tsv_file}", flush=True)


if __name__ == "__main__":
    main()
