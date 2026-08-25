#!/usr/bin/env python3
"""
Tier-2 grader contracts (round-2 playbook Phase 3 / "Implementation Contracts
for Missing Graders") — Session 11 follow-up 5.

Three deterministic graders the round-1 report flagged as missing from the
arena's positive-execution-only rubric (py_import / py_stdout never verify
the ABSENCE of side effects):

1. `grade_negative_constraint` — the model edits ONE function in a
   multi-function file but must NOT touch a designated function. The grader
   parses the returned file into an AST, isolates the preserved function's
   node, hashes its UNPARSED string representation (ast.unparse — immune to
   whitespace / quote-style / comment drift) and compares against the hash
   of the original. Any divergence fails the task regardless of execution
   success (playbook §"Negative-Constraint Grader").

2. `grade_hidden_pytest` — the prompt exposes a PUBLIC test suite (basic
   shapes); the grader executes ONLY a hidden pytest suite with aggressive
   edge cases / boundary inputs. A model that hardcodes the public answers
   fails the hidden run (playbook §"Hidden-Pytest-Suite Grader").

3. `grade_stateful_api` — the model writes a client that must interact with
   a mock API in an exact SEQUENCE with exact JSON payloads. The grader
   starts a recording local HTTP server (ephemeral port), injects the live
   URL via a config fixture, runs the client, then verifies the recorded
   request sequence + bodies (playbook §"Stateful API Grader").

All three follow the arena grading contract: return (passed: bool, note: str),
are 100% deterministic (no LLM-as-judge), and run inside a fresh /dev/shm
sandbox. Stdlib-only (http.server for the mock API, ast + hashlib for the
AST gate, pytest via `python -m pytest` if available for hidden tests —
with a pure-unittest fallback so the grader never depends on pytest being
installed on a fresh host).

Reference solutions + sabotage cases are regression-tested inline in
tests/test_grader_contracts.py (no separate corpus yet — the contracts will
be populated with real tasks during the Tier-3 corpus expansion).
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PYTEST_AVAILABLE = True
try:
    import pytest  # noqa: F401
except Exception:
    PYTEST_AVAILABLE = False


def _sandbox(prefix: str) -> Path:
    d = Path(f"/dev/shm/grader_{os.getpid()}_{re.sub(r'[^A-Za-z0-9_-]', '_', prefix)}")
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _run(d: Path, cmd, timeout: int = 60):
    try:
        res = subprocess.run(cmd, capture_output=True, text=True,
                             timeout=timeout, cwd=str(d))
        return res.returncode, res.stdout, res.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"
    except Exception as err:
        return -2, "", str(err)


# ── 1. Negative-constraint (AST-hash) grader ────────────────────────────────
def _func_ast_sha(source: str, func_name: str):
    """sha256 of the unparsed AST for `func_name` in `source`. Returns
    (digest, err). unparse normalizes whitespace/quotes/comments so cosmetic
    drift never trips the hash; a genuinely different body always does."""
    try:
        tree = ast.parse(source)
    except SyntaxError as err:
        return None, f"SYNTAX_ERROR {err.lineno}: {err.msg}"
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                and node.name == func_name:
            body = ast.unparse(node)
            return hashlib.sha256(body.encode("utf-8")).hexdigest(), ""
    return None, f"FUNC_NOT_FOUND {func_name}"


def grade_negative_constraint(code: str, grader: dict) -> tuple:
    """(passed, note). `grader` keys:
        module        name of the module file (default 'solution')
        fixtures      {path: original source} — the ORIGINAL multi-function file
        preserve      [func names that must be byte-AST-identical]
        changed       [func names that must have DIFFERENT ASTs] (optional)
        test_code     hidden test exercising the changed function (optional)
    """
    module = str(grader.get("module", "solution"))
    fixtures = grader.get("fixtures") or {}
    preserve = [str(x) for x in grader.get("preserve", [])]
    changed = [str(x) for x in grader.get("changed", [])]
    d = _sandbox(f"negconstraint_{module}")
    try:
        # 1. hash the preserved functions in the ORIGINAL fixture
        if not fixtures:
            return False, "no fixtures (original file missing)"
        orig_src = ""
        for name, content in fixtures.items():
            p = d / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            if name.endswith(".py") and name == f"{module}.py":
                orig_src = content
        if not orig_src:
            return False, f"fixture for module {module}.py missing"
        orig_hashes = {}
        for fn in preserve:
            h, err = _func_ast_sha(orig_src, fn)
            if err:
                return False, f"original {err}"
            orig_hashes[fn] = h

        # 2. write the MODEL's version and hash the same functions
        (d / f"{module}.py").write_text(code, encoding="utf-8")
        got_hashes = {}
        for fn in preserve:
            h, err = _func_ast_sha(code, fn)
            if err:
                return False, f"candidate {err}"
            got_hashes[fn] = h

        # 3. preserve gate: untouched functions must hash IDENTICAL
        for fn in preserve:
            if got_hashes[fn] != orig_hashes[fn]:
                return False, f"NEGATIVE_CONSTRAINT_VIOLATION {fn} was modified"
        # 4. changed gate (optional): the intended target must actually differ
        for fn in changed:
            h, err = _func_ast_sha(code, fn)
            if err:
                return False, f"candidate {err}"
            orig_h, orig_err = _func_ast_sha(orig_src, fn)
            if orig_err:
                # function absent from the original: adding it IS a change
                continue
            if h == orig_h:
                return False, f"EXPECTED_CHANGE_MISSING {fn} unchanged"
        # 5. optional hidden test on the edited module
        if grader.get("test_code"):
            (d / f"test_{module}.py").write_text(grader["test_code"], encoding="utf-8")
            rc, out, err = _run(d, [sys.executable, f"test_{module}.py"])
            if rc != 0:
                return False, f"hidden test rc={rc} {_norm(err)[:140] or _norm(out)[:140]}"
        return True, f"preserve={preserve} unchanged"
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ── 2. Hidden-pytest grader ─────────────────────────────────────────────────
def grade_hidden_pytest(code: str, grader: dict) -> tuple:
    """(passed, note). `grader` keys:
        module        module name the code is written to (default 'solution')
        hidden_tests  the FULL hidden pytest source (aggressive edge cases)
        fixtures      extra sandbox files (e.g. data fixtures)
    """
    module = str(grader.get("module", "solution"))
    hidden = str(grader.get("hidden_tests", ""))
    if not hidden.strip():
        return False, "no hidden tests provided"
    d = _sandbox(f"hiddenpytest_{module}")
    try:
        for name, content in (grader.get("fixtures") or {}).items():
            p = d / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
        (d / f"{module}.py").write_text(code, encoding="utf-8")
        (d / "test_hidden.py").write_text(hidden, encoding="utf-8")
        if PYTEST_AVAILABLE:
            rc, out, err = _run(d, [sys.executable, "-m", "pytest", "-q",
                                    "--tb=line", "test_hidden.py"])
        else:
            # pytest-less fallback: a generated runner execs the hidden file and
            # runs every callable test_* function, counting failures and
            # requiring >= 1 test found. Never a silent pass (a bare pytest-style
            # file otherwise executes nothing and exits 0).
            runner = (
                "import sys, traceback\n"
                "g = {}\n"
                "exec(compile(open('test_hidden.py').read(), 'test_hidden.py', "
                "'exec'), g)\n"
                "tests = sorted(n for n in g if n.startswith('test_')"
                " and callable(g[n]))\n"
                "if not tests:\n"
                "    print('NO_TESTS_FOUND')\n"
                "    sys.exit(2)\n"
                "fails = 0\n"
                "for name in tests:\n"
                "    try:\n"
                "        g[name]()\n"
                "    except Exception:\n"
                "        fails += 1\n"
                "        print('FAIL ' + name)\n"
                "        traceback.print_exc()\n"
                "sys.exit(1 if fails else 0)\n"
            )
            (d / "_run_hidden.py").write_text(runner, encoding="utf-8")
            rc, out, err = _run(d, [sys.executable, "_run_hidden.py"])
            if rc == 2:
                return False, "hidden tests found no test_* functions"
        if rc == 0:
            return True, "hidden pytest green"
        tail = (out or err).strip().splitlines()
        last = "\n".join(tail[-4:]) if tail else ""
        return False, f"hidden pytest rc={rc} {last[:160]}"
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ── 3. Stateful mock-API grader ─────────────────────────────────────────────
class _RecordingHandler(BaseHTTPRequestHandler):
    """Records (method, path, json-body) for every request and replies from
    the canned responses map. The server binds loopback only. Note: `calls` /
    `responses` are class-level because http.server instantiates handlers per
    request; grading is strictly sequential and each grade_stateful_api call
    resets `.calls`, so this is safe today (a future threaded/parallel grader
    would need per-run state)."""

    calls: list = []
    responses: dict = {}

    def log_message(self, *a):  # silence the access log
        pass

    def _record(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length).decode("utf-8", "replace") if length else ""
        try:
            body = json.loads(raw) if raw else None
        except Exception:
            body = raw
        self.calls.append({"method": self.command, "path": self.path, "body": body})

    def _reply(self):
        key = f"{self.command} {self.path}"
        resp = self.responses.get(key) or self.responses.get(self.command) or {}
        status = int(resp.get("status", 200))
        payload = resp.get("json")
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_response(status)
            self.end_headers()

    def do_GET(self):
        self._record()
        self._reply()

    def do_POST(self):
        self._record()
        self._reply()

    def do_PUT(self):
        self._record()
        self._reply()

    def do_DELETE(self):
        self._record()
        self._reply()

    def do_PATCH(self):
        self._record()
        self._reply()


def grade_stateful_api(code: str, grader: dict) -> tuple:
    """(passed, note). `grader` keys:
        module          client module name (default 'client')
        config_module   module that must expose API_BASE (default 'config')
        expected_calls  ordered [{method, path, body_contains?}] the client
                        must make — exact sequence, exact path+method, and
                        (when body_contains) a subset-match on the JSON body
        responses       {"METHOD path": {"json": {...}, "status": 200}}
        fixtures        extra sandbox files

    Only the recording SERVER is restricted to loopback; the model's client
    subprocess has normal network egress (same trust level as every other arena
    sandbox, which runs arbitrary model code too)."""
    module = str(grader.get("module", "client"))
    config_module = str(grader.get("config_module", "config"))
    expected = list(grader.get("expected_calls") or [])
    if not expected:
        return False, "no expected_calls"
    d = _sandbox(f"statefulapi_{module}")
    server = None
    try:
        for name, content in (grader.get("fixtures") or {}).items():
            p = d / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
        # ephemeral-port recording server (loopback only)
        _RecordingHandler.calls = []
        _RecordingHandler.responses = grader.get("responses") or {}
        server = ThreadingHTTPServer(("127.0.0.1", 0), _RecordingHandler)
        port = server.server_address[1]
        th = threading.Thread(target=server.serve_forever, daemon=True)
        th.start()
        # inject the live URL via the config fixture the task prompt references
        (d / f"{config_module}.py").write_text(
            f'API_BASE = "http://127.0.0.1:{port}"\n', encoding="utf-8")
        (d / f"{module}.py").write_text(code, encoding="utf-8")
        rc, out, err = _run(d, [sys.executable, f"{module}.py"], timeout=45)
        server.shutdown()
        calls = list(_RecordingHandler.calls)
        if rc != 0:
            return False, f"client rc={rc} {_norm(err)[:140] or _norm(out)[:140]}"
        # sequence + payload match
        if len(calls) != len(expected):
            got = [(c["method"], c["path"]) for c in calls]
            exp = [(e["method"], e["path"]) for e in expected]
            return False, f"call count {len(calls)}!={len(expected)} got={got} exp={exp}"
        for i, (call, exp) in enumerate(zip(calls, expected)):
            if call["method"] != exp.get("method") or call["path"] != exp.get("path"):
                return False, (f"call {i} {call['method']} {call['path']} "
                               f"!= exp {exp.get('method')} {exp.get('path')}")
            contains = exp.get("body_contains")
            if contains:
                body = call.get("body") or {}
                for k, v in contains.items():
                    if body.get(k) != v:
                        return False, (f"call {i} body {json.dumps(body)[:120]} "
                                       f"missing {k}={v!r}")
        return True, f"{len(calls)} calls in exact sequence"
    finally:
        if server:
            try:
                server.shutdown()
                server.server_close()
            except Exception:
                pass
        shutil.rmtree(d, ignore_errors=True)


# ── shared helpers ──────────────────────────────────────────────────────────
def _norm(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()


def grade_contract(task: dict, code: str) -> tuple:
    """Dispatch a Tier-2 contract grader. `task['grader']['type']` is one of
    negative_constraint / hidden_pytest / stateful_api. Mirrors the arena
    grade_task contract: returns (passed, note)."""
    gtype = str(task.get("grader", {}).get("type", ""))
    if gtype == "negative_constraint":
        return grade_negative_constraint(code, task["grader"])
    if gtype == "hidden_pytest":
        return grade_hidden_pytest(code, task["grader"])
    if gtype == "stateful_api":
        return grade_stateful_api(code, task["grader"])
    return False, f"unknown contract grader {gtype}"
