#!/usr/bin/env python3
"""
Edge Agent Arena — Benchmark Runner (Cluster 09)
================================================
Runs the 8 existing research clusters (exact research llama-server flags from
registry.yaml + research-mandated extras) against 9 hardware-tweaked agentic
benchmark families defined in researches/09-agent-arena-bench/tasks.json:

  1. Terminal Bench 2.1        6. Agents' Last Exam
  2. NL2Repo                   7. AutomationBench (Public)
  3. Cybergym                  8. DSBench-FullStack
  4. DeepSWE                   9. DSBench-Hard
  5. Toolathlon-Verified

Fairness lock:
  - EXACT research launch flags (build_llama_server_cmd), never deviates.
  - Deterministic grading: sandboxed execution (/dev/shm), unit tests, JSON
    validation, numeric tolerance. No LLM-as-judge.
  - temperature=0.1, one pass@1 attempt per task, same prompt order everywhere.
  - VRAM safety: prompt+max_tokens capped below 0.9*context_length; a cluster
    whose server fails to start is recorded as an all-fail run (never skipped).
  - No aider, no old benchmarks.

Outputs (overwritten every run):
  latest/arena_results.json
  latest/arena_results.tsv
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.llamacpp_cluster_runner import build_llama_server_cmd, cleanup_port
from tests.human_repeatability_eval import (
    measure_gpu_vram,
    extract_code_block,
)

TOTAL_VRAM_MB = 6144            # RTX 3050 6GB envelope
HEADROOM_FLOOR_MB = 1331        # ~1.3 GB mandatory free headroom
TASKS_FILE = PROJECT_ROOT / "researches" / "09-agent-arena-bench" / "tasks.json"
LATEST_DIR = PROJECT_ROOT / "latest"

DEFAULT_SYSTEM = (
    "You are an expert AI software engineer running on constrained edge hardware. "
    "Generate ONLY valid, minimal, self-contained code or the exact requested answer. "
    "Zero conversational fluff."
)

# Phase-2 backport (Session 9): the measured-best rescue style from the
# phase2_prompt_sweep sweep (self-analyse rescued 17/30 failures). Appended to
# DEFAULT_SYSTEM BY DEFAULT (Session 9 follow-up: --self-analyse promoted to
# the default — fleet pass@1 63.9 -> 72.7 from one prompt line, never regresses
# beyond sampling noise) so the pass@1 prompt keeps the frozen arena contract
# and gains the self-test behavior. --no-self-analyse reverts to the bare
# frozen prompt — the exact analogue of harness.py's --self-analyse flag.
SELF_ANALYSE_DIRECTIVE = (
    "Before answering, mentally run the artifact against the grader's likely "
    "checks (fixtures, imports, exact output, numeric tolerance) and correct "
    "it in your head. Then output ONLY the final corrected artifact."
)


def query_completion(server_url, prompt_text, system_instruction=None, max_tokens=256, timeout=120):
    """
    Local /v1/chat/completions query with a generous timeout (default 120 s) so a
    slow-but-correct cluster is never unfairly failed by a truncated generation.
    The shared human_repeatability_eval.query_llama_completion hardcodes 30 s and
    must stay untouched for the other harnesses — this wrapper is arena-specific.
    Returns (content, ttft_ms, tok_per_sec). Empty content on any error/timeout.
    """
    url = f"{server_url}/v1/chat/completions"
    sys_msg = system_instruction or DEFAULT_SYSTEM
    payload = json.dumps({
        "messages": [
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": prompt_text},
        ],
        "temperature": 0.1,
        "max_tokens": max_tokens,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    start_t = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            elapsed = time.time() - start_t
            content = data["choices"][0]["message"]["content"]
            timings = data.get("timings", {})
            ttft_ms = round(timings.get("prompt_ms", elapsed * 1000.0), 1)
            tok_per_sec = round(timings.get("predicted_per_second",
                                           len(content.split()) / max(elapsed, 0.001)), 1)
            return content, ttft_ms, tok_per_sec
    except Exception:
        return "", 0.0, 0.0


# ── Loading ──────────────────────────────────────────────────────────────────
def load_registry():
    import yaml
    with open(PROJECT_ROOT / "registry.yaml", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    clusters = list(data.get("clusters", []))
    # Experiments overlay (mirrors phase2_prompt_sweep.load_registry_clusters):
    # the REAL-Gemma ceiling probes (e2 = E2B, e3 = E4B, plus e21/e22 Hermes
    # rows) live in experiments.yaml, NOT the certified registry. Best-effort:
    # a missing/malformed experiments.yaml degrades to registry-only, so the
    # certified arena contract stays intact.
    exp_path = PROJECT_ROOT / "researches" / "09-agent-arena-bench" / \
        "experiments.yaml"
    if exp_path.exists():
        try:
            with open(exp_path, encoding="utf-8") as fh:
                exps = yaml.safe_load(fh) or {}
            clusters.extend(exps.get("clusters", []))
        except (yaml.YAMLError, OSError):
            pass
    return clusters


def load_tasks():
    with open(TASKS_FILE) as f:
        return json.load(f)


def build_optimization_string(cluster_cfg):
    """Short human-readable optimization description for report col 1."""
    env = cluster_cfg.get("benchmark_env", {})
    parts = [f"ctx {env.get('context_length', 4096)}"]
    if env.get("cache_type_k"):
        parts.append(f"KV {env['cache_type_k']}/{env.get('cache_type_v', 'q8_0')}")
    if env.get("flash_attn"):
        parts.append("flash-attn")
    if cluster_cfg["id"] in ("cluster1", "cluster5") and env.get("lora_path"):
        parts.append("LoRA")
    if cluster_cfg["id"] in ("cluster2", "cluster3", "cluster4"):
        parts.append("mlock")
    parts.append(f"ngl {env.get('n_gpu_layers', 99)}")
    return " · ".join(parts)


# ── Server lifecycle (distrobox-aware, like human_repeatability_eval) ───────
def start_server(cluster_cfg):
    """Start llama-server with EXACT research flags. Returns (proc, port) or (None, port)."""
    cmd, port = build_llama_server_cmd(cluster_cfg)
    cleanup_port(port)
    time.sleep(1)

    lib_path = str(PROJECT_ROOT / "llama.cpp" / "build" / "bin")
    env_setup = f"export LD_LIBRARY_PATH={lib_path}:$LD_LIBRARY_PATH; "
    shell_cmd = env_setup + " ".join(f"'{a}'" if " " in a else a for a in cmd)

    if shutil.which("distrobox"):
        full = ["distrobox", "enter", "ws-ai", "--", "sh", "-c", shell_cmd]
    else:
        full = ["sh", "-c", shell_cmd]

    print(f"⚙️  Launching llama-server (research flags) on port {port} for {cluster_cfg['id']}...", flush=True)
    proc = subprocess.Popen(full, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{port}/v1/models"

    for _ in range(120):
        if proc.poll() is not None:
            print(f"❌ llama-server for {cluster_cfg['id']} exited early (CUDA OOM / bad model) — recording all-fail.", flush=True)
            return None, port
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    print(f"✅ Healthy on port {port}.", flush=True)
                    return proc, port
        except Exception:
            time.sleep(1)
    print(f"⚠️  Health-check timeout for {cluster_cfg['id']} on port {port}.", flush=True)
    return proc, port


def stop_server(proc, port):
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
    cleanup_port(port)
    time.sleep(1)


# ── Sandboxed graders (100% deterministic) ──────────────────────────────────
def _sandbox(task_id):
    d = Path(f"/dev/shm/arena_{os.getpid()}_{re.sub(r'[^A-Za-z0-9_-]', '_', task_id)}")
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _write_fixtures(d, fixtures):
    for name, content in (fixtures or {}).items():
        p = d / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")


def _norm(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _strip_fences(text):
    """Remove a ```...``` fenced block (the arena answer format) so
    exact-string/numeric graders see the VALUE the model wrapped. Follow-up-13:
    AL-02 failed 4 attempts on out='```text 255.255.255.192```' — the content
    was correct, the fence was noise. Handles inline (```lang VALUE```) and
    multiline (```lang\nVALUE\n```) fences; a lone unclosed fence drops the
    opening marker and keeps the rest."""
    t = str(text or "")
    # multiline fenced block: ```lang\n...\n```
    m = re.search(r"```[^\n]*\n(.*?)```", t, re.DOTALL)
    if m:
        return m.group(1)
    # inline fenced block: ```lang VALUE```  (or bare ```VALUE```)
    m = re.search(r"```[^\n]*?\s(.*?)```", t, re.DOTALL)
    if m:
        return m.group(1)
    m = re.search(r"```(.*?)```", t, re.DOTALL)
    if m:
        return m.group(1)
    # unclosed fence: drop the opening marker (up to the first space OR
    # newline — a greedy [^\n]* would eat the value on a no-newline marker
    # line, e.g. '```text 255.255.255.192' -> '' (reviewer f14 catch)
    if t.count("```") % 2 == 1:
        t = re.sub(r"```[^\n]*?[\s\n]", "", t, count=1)
    return t


def _extract_first_number(text):
    # Comma/currency tolerant: "1,476.00" or "$1,240" must extract cleanly.
    t = re.sub(r"[,$]", "", str(text or ""))
    m = re.search(r"-?\d+(?:\.\d+)?", t)
    return float(m.group(0)) if m else None


def _strip_reasoning_tags(text):
    """Remove <think>/<thought> reasoning blocks (and any stray tags) that
    reasoning models (e.g. qwen3.6-4b) emit before their real answer.
    Applied to ALL clusters before grading so no model is unfairly failed."""
    t = re.sub(r"<(?:think|thought)>.*?</(?:think|thought)>", "", str(text or ""), flags=re.DOTALL)
    t = re.sub(r"</?(?:think|thought)>", "", t)
    return t.strip()


def _run_in(d, cmd, timeout=30):
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=str(d))
        return res.returncode, res.stdout, res.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"


def grade_task(task, raw_output, sandbox_dir=None, artifact_name=None,
               write_fixtures=True):
    """Deterministic grade for one task. Returns (passed: bool, note: str).

    `sandbox_dir` (Benchmark-2 project mode, 2026-08-09): when given, grade
    INSIDE that persistent directory instead of a throwaway /dev/shm sandbox
    (no wipe, no cleanup). Project steps accumulate artifacts (module files,
    output files) in one shared repo dir so step N+1 sees step N's state; the
    caller seeds the union of all steps' fixtures once. Default None keeps
    the certified behavior byte-identical (fresh sandbox per attempt).

    `artifact_name` (project mode): base filename for this step's artifact
    (bash -> {name}.sh, py_stdout/py_state -> {name}.py; py_import keeps the
    contract module name). Distinct per step so steps never clobber each
    other's scripts in the shared repo. None = the certified defaults
    (script.sh / script.py).

    `write_fixtures` (project regression gate): False skips re-writing this
    task's fixtures — the caller seeded the union once, and the gate must
    detect when a LATER step corrupted an earlier step's data files (a
    fixture re-write would mask that). Default True = certified behavior."""
    grader = task.get("grader", {})
    gtype = grader.get("type")

    # Tier-2 canary gate (round-2 playbook §"Canary sequence", Session 11
    # follow-up 6): when a task's grader carries a canary UUID (injected into
    # the few-shot exemplar as a hidden comment), ANY output containing that
    # exact UUID is a blind verbatim copy of the exemplar string space, not
    # novel code — fail it instantly regardless of what the type grader would
    # say (proven-copy is a hygiene violation, not a format miss).
    canary = grader.get("canary")
    if canary:
        from tests.canary import canary_leak_note, scan_output
        if scan_output(raw_output, str(canary)):
            return False, canary_leak_note(str(canary))

    # Real-project clarification oracle (Benchmark-2 tier, 2026-08-09): an
    # underspecified step may carry grader.clarify = {keywords, answer}. If
    # the model's output looks like a CLARIFYING QUESTION about the
    # underspecified requirement (a '?' + at least one keyword), the grader
    # returns the ORACLE answer as the note — the adaptive loop then feeds it
    # into the next attempt (ask → get answer → implement), exactly like a
    # developer asking the product owner. A non-asking model is graded by the
    # type grader normally (the documented alternative format still passes) —
    # asking is recorded as a quality signal, never a pass gate.
    clarify = grader.get("clarify") if isinstance(grader, dict) else None
    if clarify and isinstance(clarify, dict) and clarify.get("keywords"):
        from tests.arena_clarify import is_clarifying_question
        if is_clarifying_question(raw_output, clarify):
            return False, f"CLARIFY: {clarify.get('answer', '')}"

    if gtype in ("bash_stdout", "bash_state"):
        code = extract_code_block(raw_output, "bash", is_dual_mode=False).strip()
        if not code:
            return False, "no bash code extracted"
        d = _sandbox(task["id"]) if sandbox_dir is None else Path(sandbox_dir)
        try:
            if write_fixtures:
                _write_fixtures(d, grader.get("fixtures"))
            script = f"{artifact_name or 'script'}.sh"
            (d / script).write_text(code, encoding="utf-8")
            rc, out, err = _run_in(d, ["bash", script])
            if gtype == "bash_stdout":
                mode = grader.get("mode", "exact")
                if mode == "exact":
                    passed = _norm(out) == _norm(grader.get("expected", ""))
                    return passed, f"rc={rc} out={_norm(out)[:80]!r}"
                return False, f"unknown mode {mode}"
            # bash_state
            missing = [f for f in grader.get("expected_files", []) if not (d / f).exists()]
            stray = [f for f in grader.get("absent_files", []) if (d / f).exists()]
            passed = rc == 0 and not missing and not stray
            note = f"rc={rc} missing={missing} stray={stray}"
            return passed, note
        except Exception as e:
            return False, f"grading error {e}"
        finally:
            if sandbox_dir is None:
                shutil.rmtree(d, ignore_errors=True)

    if gtype == "py_import":
        code = extract_code_block(raw_output, "python", is_dual_mode=False).strip()
        if not code:
            return False, "no python code extracted"
        module = grader.get("module", "solution")
        d = _sandbox(task["id"]) if sandbox_dir is None else Path(sandbox_dir)
        try:
            # Real-project tier (2026-08-09): dotted module names are PACKAGE
            # paths (pipeline.load -> pipeline/load.py). Certified 108 tasks
            # use flat names only, so this is additive (byte-identical there).
            mod_path = d / (module.replace(".", "/") + ".py")
            mod_path.parent.mkdir(parents=True, exist_ok=True)
            mod_path.write_text(code, encoding="utf-8")
            (d / f"test_{module}.py").write_text(grader.get("test_code", ""), encoding="utf-8")
            rc, out, err = _run_in(d, [sys.executable, f"test_{module}.py"], timeout=30)
            passed = rc == 0
            # EXCEPTION-LINE note (S13, 2026-08-09): a py_import failure's
            # stderr is a traceback whose FIRST 120 chars are the header +
            # file path ("Traceback (most recent call last): File \"/var/…")
            # and whose ACTIONABLE part is the FINAL line ("TypeError: object
            # is not iterable", "SyntaxError: invalid syntax"). The note is
            # fed back into the model's next attempt, so head-truncation made
            # the error feedback useless. Take the LAST non-empty stderr line
            # (the exception itself), with a Traceback marker when a traceback
            # header exists (keeps classify_failure → run_error). Deliberately
            # NOT the raw tail: a caret/source line above the exception can
            # carry echoed task text, which must never leak into the fresh
            # anti-echo turn (test_run_cell_echo… regression guard).
            err_lines = [ln.strip() for ln in (err or "").splitlines() if ln.strip()]
            if err_lines:
                tail = _norm(err_lines[-1])[-120:]
                if "traceback" in (err or "").lower():
                    tail = f"Traceback ... {tail}"
                note = f"rc={rc} {tail}"
            else:
                note = f"rc={rc} {_norm(out)[-120:]}"
            return passed, note
        except Exception as e:
            return False, f"grading error {e}"
        finally:
            if sandbox_dir is None:
                shutil.rmtree(d, ignore_errors=True)

    if gtype == "py_state":
        code = extract_code_block(raw_output, "python", is_dual_mode=False).strip()
        if not code:
            return False, "no python code extracted"
        d = _sandbox(task["id"]) if sandbox_dir is None else Path(sandbox_dir)
        try:
            if write_fixtures:
                _write_fixtures(d, grader.get("fixtures"))
            script = f"{artifact_name or 'script'}.py"
            (d / script).write_text(code, encoding="utf-8")
            rc, out, err = _run_in(d, [sys.executable, script], timeout=30)
            if rc != 0:
                return False, f"run rc={rc} {_norm(err)[:120]}"
            for fname, exp_lines in (grader.get("expected_file_content") or {}).items():
                p = d / fname
                if not p.exists():
                    return False, f"missing {fname}"
                got = [ln.strip() for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
                exp = [str(x).strip() for x in exp_lines]
                if got != exp:
                    return False, f"{fname} got={got} exp={exp}"
            return True, "state ok"
        except Exception as e:
            return False, f"grading error {e}"
        finally:
            if sandbox_dir is None:
                shutil.rmtree(d, ignore_errors=True)

    if gtype == "py_stdout":
        code = extract_code_block(raw_output, "python", is_dual_mode=False).strip()
        if not code:
            return False, "no python code extracted"
        d = _sandbox(task["id"]) if sandbox_dir is None else Path(sandbox_dir)
        try:
            if write_fixtures:
                _write_fixtures(d, grader.get("fixtures"))
            script = f"{artifact_name or 'script'}.py"
            (d / script).write_text(code, encoding="utf-8")
            rc, out, err = _run_in(d, [sys.executable, script], timeout=30)
            if rc != 0:
                return False, f"run rc={rc} {_norm(err)[:120]}"
            mode = grader.get("mode", "exact")
            if mode == "numeric":
                # S14-5: strip a wrapping ```...``` fence BEFORE extracting the
                # first number (symmetric with exact_string's S14-1 fix).
                # _extract_first_number is fence-TOLERANT on a bare fenced
                # value (the value is the first number either way), but a
                # fence LANG-TAG with embedded digits corrupts it: on
                # '```c99\n1140.96\n```' the un-stripped text's first number
                # is 99 (from "c99"), failing a correct answer. Stripping
                # removes the marker so the number inside is the one graded;
                # no fence -> no-op, so the cost is zero.
                got = _extract_first_number(_strip_fences(out))
                exp = float(grader.get("expected", 0))
                tol = float(grader.get("tolerance", 0.01))
                passed = got is not None and abs(got - exp) <= tol
                return passed, f"got={got} exp={exp}"
            if mode == "exact_string":
                case = grader.get("case_sensitive", True)
                # follow-up-13: strip a wrapping ```...``` fence (AL-02 emitted
                # '```text 255.255.255.192```' — the content was right, the
                # fence was noise that _norm alone can't remove)
                got_s = _norm(_strip_fences(out))
                exp_s = _norm(grader.get("expected", ""))
                passed = got_s == exp_s if case else got_s.lower() == exp_s.lower()
                return passed, f"out={got_s[:80]!r}"
            if mode == "lines_set":
                got_set = {ln.strip() for ln in out.splitlines() if ln.strip()}
                exp_set = {str(x).strip() for x in grader.get("expected", [])}
                passed = got_set == exp_set
                # follow-up-11: include exp= so the adaptive loop can
                # self-correct (AB-03 was stuck for 4 attempts on a bare
                # got=[...] with no target — the model couldn't see it was
                # missing the leading slash + POST /api).
                return passed, f"got={sorted(got_set)} exp={sorted(exp_set)}"
            if mode == "lines_numeric":
                exp_map = {str(k).strip().lower(): float(v) for k, v in grader.get("expected", {}).items()}
                tol = float(grader.get("tolerance", 0.01))
                got_map = {}
                for ln in out.splitlines():
                    ln = ln.strip()
                    if not ln:
                        continue
                    if ":" in ln:
                        k, v = ln.split(":", 1)
                        got_map[k.strip().lower()] = _extract_first_number(v)
                if set(got_map) != set(exp_map):
                    return False, f"keys mismatch got={sorted(got_map)} exp={sorted(exp_map)}"
                for k, ev in exp_map.items():
                    if got_map[k] is None or abs(got_map[k] - ev) > tol:
                        return False, f"{k}: got={got_map[k]} exp={ev}"
                return True, "lines numeric match"
            return False, f"unknown mode {mode}"
        except Exception as e:
            return False, f"grading error {e}"
        finally:
            if sandbox_dir is None:
                shutil.rmtree(d, ignore_errors=True)

    if gtype == "json_tool_call":
        obj = _extract_json_object(raw_output)
        if obj is None:
            return False, "no JSON object found"
        name = str(obj.get("name", obj.get("tool", ""))).lower()
        args = obj.get("arguments", obj.get("args", {}))
        if not isinstance(args, dict):
            return False, "arguments not an object"
        if name != grader.get("expected_name", "").lower():
            return False, f"tool={name} exp={grader.get('expected_name')}"
        for k, v in grader.get("required_args", {}).items():
            got = str(args.get(k, "")).lower()
            if str(v).lower() not in got:
                return False, f"arg {k}: {got!r} missing {v!r}"
        return True, "tool call ok"

    if gtype == "json_tool_call_array":
        arr = _extract_json_array(raw_output)
        if arr is None or not isinstance(arr, list):
            return False, "no JSON array found"
        names = [str(c.get("name", c.get("tool", ""))).lower() for c in arr]
        exp_names = [str(n).lower() for n in grader.get("expected_names", [])]
        if names != exp_names:
            return False, f"names={names} exp={exp_names}"
        for i, req in enumerate(grader.get("required_args", [])):
            args = arr[i].get("arguments", arr[i].get("args", {})) or {}
            for k, v in req.items():
                got = str(args.get(k, "")).lower()
                if str(v).lower() not in got:
                    return False, f"call {i} arg {k}: {got!r} missing {v!r}"
        return True, "tool sequence ok"

    if gtype == "numeric":
        # S14-5: fence-strip before first-number extraction (see py_stdout
        # numeric above — same rationale: a fence lang-tag's embedded digits
        # (e.g. '```c99 ...') would be grabbed as the answer's first number).
        got = _extract_first_number(_strip_fences(raw_output))
        exp = float(grader.get("expected", 0))
        tol = float(grader.get("tolerance", 0.01))
        passed = got is not None and abs(got - exp) <= tol
        return passed, f"got={got} exp={exp}"

    if gtype == "exact_string":
        case = grader.get("case_sensitive", True)
        got_s = _norm(_strip_fences(raw_output))
        exp_s = _norm(grader.get("expected", ""))
        passed = got_s == exp_s if case else got_s.lower() == exp_s.lower()
        return passed, f"out={got_s[:80]!r}"

    # Tier-2 contract graders (round-2 playbook Phase 3, Session 11
    # follow-up 5): negative-constraint AST-hash / hidden-pytest / stateful
    # mock-API. Same deterministic contract; live code extracted here and
    # handed to the contract module (grader_contracts.py).
    if gtype in ("negative_constraint", "hidden_pytest", "stateful_api"):
        from tests.grader_contracts import grade_contract
        lang = "python"
        code = extract_code_block(raw_output, lang, is_dual_mode=False).strip()
        if not code:
            return False, "no python code extracted"
        return grade_contract(task, code)

    return False, f"unknown grader {gtype}"


def _extract_json_object(text):
    t = str(text or "")
    m = re.search(r"```(?:json)?\s*(.*?)```", t, re.DOTALL)
    if m:
        t = m.group(1)
    try:
        import json as _j
        return _j.loads(t.strip())
    except Exception:
        pass
    # balanced-brace scan
    start = t.find("{")
    while start != -1:
        depth, i = 0, start
        for i in range(start, len(t)):
            if t[i] == "{":
                depth += 1
            elif t[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        import json as _j
                        return _j.loads(t[start:i + 1])
                    except Exception:
                        break
        start = t.find("{", start + 1)
    return None


def _extract_json_array(text):
    t = str(text or "")
    m = re.search(r"```(?:json)?\s*(.*?)```", t, re.DOTALL)
    if m:
        t = m.group(1)
    try:
        import json as _j
        return _j.loads(t.strip())
    except Exception:
        pass
    start = t.find("[")
    while start != -1:
        depth, i = 0, start
        for i in range(start, len(t)):
            if t[i] == "[":
                depth += 1
            elif t[i] == "]":
                depth -= 1
                if depth == 0:
                    try:
                        import json as _j
                        return _j.loads(t[start:i + 1])
                    except Exception:
                        break
        start = t.find("[", start + 1)
    return None


# ── Cluster evaluation ───────────────────────────────────────────────────────
def evaluate_cluster(cluster_cfg, benchmarks, max_tokens_per_bench=None,
                     self_analyse=True):
    key = cluster_cfg["key"]
    title = cluster_cfg["title"]
    port = cluster_cfg.get("benchmark_env", {}).get("port", 8089)
    ctx = int(cluster_cfg.get("benchmark_env", {}).get("context_length", 4096))
    system_instruction = (DEFAULT_SYSTEM + " " + SELF_ANALYSE_DIRECTIVE
                          if self_analyse else DEFAULT_SYSTEM)

    print("\n" + "=" * 72)
    print(f" 🧠 ARENA EVALUATION: {key}")
    print(f" {title} | port {port} | ctx {ctx}")
    print("=" * 72, flush=True)

    proc, port = start_server(cluster_cfg)
    if proc is None:
        # Genuine all-fail run (server could not start, e.g. CUDA OOM).
        tasks_out = []
        for bench in benchmarks:
            for t in bench["tasks"]:
                tasks_out.append({
                    "benchmark": bench["name"], "id": t["id"], "title": t["title"],
                    "passed": False, "note": "SERVER_FAIL", "latency_s": 0.0,
                    "ttft_ms": 0.0, "tok_s": 0.0,
                })
        return _build_cluster_result(cluster_cfg, benchmarks, tasks_out, server_ok=False)

    peak_vram = 0
    ttft_vals, tok_vals, lat_vals = [], [], []
    tasks_out = []
    try:
        for bench in benchmarks:
            tasks = bench["tasks"]
            if max_tokens_per_bench:
                tasks = tasks[: max_tokens_per_bench]
            for t in tasks:
                cap = max(16, int(ctx * 0.9) - 32)
                # f25 fix (mirrors phase2_prompt_sweep.run_cell): reasoning
                # models (gemma4 E2B/E4B with --reasoning on) spend their first
                # ~300-500 tokens in the thinking channel — at the default
                # 96-256 cap the ENTIRE budget dies there and content returns
                # EMPTY (deterministic 100% no_code). max_tokens_override (an
                # experiments.yaml per-cluster key) raises the cap for that
                # cluster only; certified clusters keep the frozen budget.
                mt = min(int(t.get("max_tokens", 96)), cap)
                override = cluster_cfg.get("max_tokens_override")
                if override:
                    mt = min(int(override), cap)
                start_t = time.time()
                raw, ttft, tok_s = query_completion(
                    f"http://127.0.0.1:{port}", t["prompt"],
                    system_instruction=system_instruction, max_tokens=mt,
                )
                lat = round(time.time() - start_t, 2)
                raw = _strip_reasoning_tags(raw)
                passed, note = grade_task(t, raw)
                tasks_out.append({
                    "benchmark": bench["name"], "id": t["id"], "title": t["title"],
                    "passed": passed, "note": note, "latency_s": lat,
                    "ttft_ms": round(ttft, 1), "tok_s": round(tok_s, 1),
                })
                ttft_vals.append(ttft); tok_vals.append(tok_s); lat_vals.append(lat)
                peak_vram = max(peak_vram, measure_gpu_vram())
                mark = "PASS" if passed else "FAIL"
                print(f"  [{mark}] {bench['name']:22s} {t['id']:8s} {t['title'][:52]:52s} {lat:6.1f}s", flush=True)
    finally:
        stop_server(proc, port)
        peak_vram = max(peak_vram, measure_gpu_vram())

    return _build_cluster_result(cluster_cfg, benchmarks, tasks_out, server_ok=True,
                                 ttft_vals=ttft_vals, tok_vals=tok_vals,
                                 lat_vals=lat_vals, peak_vram=peak_vram)


def _build_cluster_result(cluster_cfg, benchmarks, tasks_out, server_ok=True,
                          ttft_vals=None, tok_vals=None, lat_vals=None, peak_vram=0):
    ttft_vals = ttft_vals or []
    tok_vals = tok_vals or []
    lat_vals = lat_vals or []

    bench_scores = {}
    for bench in benchmarks:
        bt = [t for t in tasks_out if t["benchmark"] == bench["name"]]
        passed = sum(1 for t in bt if t["passed"])
        total = len(bt) or 1
        bench_scores[bench["name"]] = {"passed": passed, "total": len(bt), "score": round(100.0 * passed / total, 1)}

    scores = [s["score"] for s in bench_scores.values() if s["total"] > 0]
    overall = round(sum(scores) / len(scores), 1) if scores else 0.0

    if not server_ok:
        # Genuine all-fail run: record zero telemetry so the report never shows
        # a dead cluster with max headroom (fairness/display).
        return {
            "id": cluster_cfg["id"],
            "key": cluster_cfg["key"],
            "title": cluster_cfg["title"],
            "builder_model": cluster_cfg["builder_model"],
            "optimizations": build_optimization_string(cluster_cfg),
            "server_ok": False,
            "overall_score": overall,
            "benchmarks": bench_scores,
            "telemetry": {
                "ttft_ms": 0.0, "throughput_tok_s": 0.0, "total_latency_s": 0.0,
                "peak_vram_mb": 0, "vram_headroom_mb": 0,
            },
            "tasks": tasks_out,
        }

    headroom = max(TOTAL_VRAM_MB - peak_vram, 0) if peak_vram else 0
    if peak_vram and headroom < HEADROOM_FLOOR_MB:
        print(f"⚠️  {cluster_cfg['id']}: VRAM headroom {headroom} MB < {HEADROOM_FLOOR_MB} MB floor — check server flags.", flush=True)
    return {
        "id": cluster_cfg["id"],
        "key": cluster_cfg["key"],
        "title": cluster_cfg["title"],
        "builder_model": cluster_cfg["builder_model"],
        "optimizations": build_optimization_string(cluster_cfg),
        "server_ok": True,
        "overall_score": overall,
        "benchmarks": bench_scores,
        "telemetry": {
            "ttft_ms": round(sum(ttft_vals) / len(ttft_vals), 1) if ttft_vals else 0.0,
            "throughput_tok_s": round(sum(tok_vals) / len(tok_vals), 1) if tok_vals else 0.0,
            "total_latency_s": round(sum(lat_vals), 1),
            "peak_vram_mb": peak_vram,
            "vram_headroom_mb": headroom,
        },
        "tasks": tasks_out,
    }


# ── Save + summary ───────────────────────────────────────────────────────────
def save_results(results, benchmarks, args):
    LATEST_DIR.mkdir(parents=True, exist_ok=True)
    meta = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "hardware": f"NVIDIA GeForce RTX 3050 6GB (6144 MiB), headroom floor {HEADROOM_FLOOR_MB} MiB",
        "benchmark_order": [b["name"] for b in benchmarks],
        "smoke": bool(args.smoke),
        "max_tasks_per_bench": args.max_tasks_per_bench,
        "self_analyse": bool(args.self_analyse),
        "command": " ".join(sys.argv),
    }
    payload = {"meta": meta, "clusters": results}

    json_path = LATEST_DIR / "arena_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    header = ["cluster_key", "title", "builder_model", "optimizations"] + \
             [b["name"] for b in benchmarks] + \
             ["Overall", "peak_vram_mb", "vram_headroom_mb", "avg_ttft_ms", "avg_tok_s"]
    rows = []
    for r in sorted(results, key=lambda x: x["overall_score"], reverse=True):
        rows.append([r["key"], r["title"], r["builder_model"], r["optimizations"]] +
                    [r["benchmarks"][b["name"]]["score"] for b in benchmarks] +
                    [r["overall_score"], r["telemetry"]["peak_vram_mb"],
                     r["telemetry"]["vram_headroom_mb"], r["telemetry"]["ttft_ms"],
                     r["telemetry"]["throughput_tok_s"]])
    tsv_path = LATEST_DIR / "arena_results.tsv"
    with open(tsv_path, "w", encoding="utf-8") as f:
        f.write("\t".join(header) + "\n")
        for row in rows:
            f.write("\t".join(str(c) for c in row) + "\n")

    print(f"\n💾 Saved {json_path}")
    print(f"💾 Saved {tsv_path}")
    return json_path, tsv_path


def print_summary(results, benchmarks):
    print("\n" + "=" * 100)
    print(" 🏆 ARENA LEADERBOARD (Overall = mean of 9 benchmark scores)")
    print("=" * 100)
    header = "Cluster".ljust(46) + "".join(b["name"][:14].rjust(15) for b in benchmarks) + " Overall".rjust(10)
    print(header)
    print("-" * len(header))
    for r in sorted(results, key=lambda x: x["overall_score"], reverse=True):
        line = r["key"][:46].ljust(46)
        for b in benchmarks:
            line += str(r["benchmarks"][b["name"]]["score"]).rjust(15)
        line += str(r["overall_score"]).rjust(10)
        print(line)
    print("=" * 100)


def build_parser():
    ap = argparse.ArgumentParser(description="Edge Agent Arena benchmark runner (Cluster 09)")
    ap.add_argument("--smoke", action="store_true", help="1 task per benchmark (fast validation)")
    ap.add_argument("--max-tasks-per-bench", type=int, default=None,
                    help="Cap tasks per benchmark (overrides smoke)")
    ap.add_argument("--clusters", type=str, default="",
                    help="Comma-separated report ids or registry ids to run (default: all 8)")
    ap.add_argument("--self-analyse", action="store_true", dest="self_analyse",
                    help="[default] append the Phase-2 self-analyse directive to the system "
                         "prompt (the measured-best rescue style — Session 9; ON by default)")
    ap.add_argument("--no-self-analyse", action="store_false", dest="self_analyse",
                    help="opt out: use the frozen baseline prompt (no self-analyse directive)")
    ap.set_defaults(self_analyse=True)
    ap.add_argument("--outdir", type=str, default=None, help="Output directory (default: latest/)")
    return ap


def main():
    global LATEST_DIR
    args = build_parser().parse_args()
    if args.outdir:
        LATEST_DIR = Path(args.outdir)

    clusters = load_registry()
    if args.clusters:
        want = {c.strip().lower() for c in args.clusters.split(",")}
        clusters = [c for c in clusters
                    if c["id"].lower() in want
                    or c["id"].replace("cluster", "").zfill(2) in want
                    or c["key"].split("-")[0].zfill(2) in want]

    tasks_data = load_tasks()
    benchmarks = tasks_data["benchmarks"]
    mpt = args.max_tasks_per_bench or (1 if args.smoke else None)

    results = []
    for cluster in clusters:
        results.append(evaluate_cluster(cluster, benchmarks,
                                        max_tokens_per_bench=mpt,
                                        self_analyse=args.self_analyse))

    json_path, tsv_path = save_results(results, benchmarks, args)
    print_summary(results, benchmarks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
