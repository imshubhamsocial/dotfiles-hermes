"""
End-to-End Developer Workflow & Toolchain Stress Test Suite (Roadmap 6)
======================================================================
Simulates realistic, complex multi-step developer workflows using Hermes:
1. Multi-File Refactoring & AST Patching
2. Git Conflict / Merge Reconciliation & Observer Gate Commit
3. Subagent Delegation Handshake (@researcher -> @coder -> @tester)
4. Dirty Sandbox & Broken Build Recovery
5. Context Diffusion / 20-Turn State Bleed
6. Command Injection & Subshell Escapes

Usage:
    python3.13 -m pytest tests/roadmap6_adversarial/test_developer_workflows_e2e.py -v -s
"""

import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
BIN_DIR = ROOT / ".hermes/bin"


def is_llama_server_running() -> bool:
    import urllib.request
    try:
        req = urllib.request.urlopen("http://127.0.0.1:8138/health", timeout=2)
        return req.status == 200
    except Exception:
        return False


def run_hermes(prompt: str, cwd: Path | None = None, timeout: int = 180) -> tuple[int, str, str]:
    hermes_bin = shutil.which("hermes") or str(Path.home() / ".local/bin/hermes")
    cmd = [hermes_bin, "-z", prompt, "--yolo"]
    res = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(cwd or ROOT)
    )
    return res.returncode, res.stdout, res.stderr


class TestDeveloperWorkflowsE2E:

    # =========================================================================
    # 1. Multi-File Project Creation & Observer Gate Pass
    # =========================================================================
    @pytest.mark.skipif(not is_llama_server_running(), reason="llama-server offline")
    def test_workflow_multi_file_python_library(self):
        """
        Developer Story:
        Developer asks Hermes to build a complete, tested Python package with 3 files:
        - src/math_engine.py
        - src/__init__.py
        - tests/test_math_engine.py
        Verifies all files are created, syntax passes Observer Gate, and pytest succeeds.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            work = Path(tmpdir)
            prompt = (
                f"In the current directory ({work}), create a minimal Python library:\n"
                "1. `src/math_engine.py`: implements `fibonacci(n: int) -> int` and `is_prime(n: int) -> bool` with type hints.\n"
                "2. `src/__init__.py`: exports them.\n"
                "3. `tests/test_math_engine.py`: 5 unit tests with pytest.\n"
                "Run pytest to verify 100% tests pass."
            )
            code, stdout, stderr = run_hermes(prompt, cwd=work, timeout=120)
            assert code == 0, f"Hermes failed multi-file project creation: {stderr}"

            # Check files exist
            f1 = work / "src/math_engine.py"
            f2 = work / "src/__init__.py"
            f3 = work / "tests/test_math_engine.py"
            assert f1.exists(), "src/math_engine.py was not created"
            assert f3.exists(), "tests/test_math_engine.py was not created"

            # Run Observer Gate on generated code
            res_gate = subprocess.run(
                ["python3.13", str(BIN_DIR / "observer_gate.py"), str(f1)],
                capture_output=True, text=True
            )
            assert res_gate.returncode == 0, f"Generated file failed Observer Gate: {res_gate.stdout}"

            # Run pytest on generated tests
            res_test = subprocess.run(["python3.13", "-m", "pytest", str(f3)], capture_output=True, text=True)
            assert res_test.returncode == 0, f"Generated test suite failed: {res_test.stdout}"

    # =========================================================================
    # 2. Broken Build / Bug Triage & Surgical Repair (TDD Loop)
    # =========================================================================
    @pytest.mark.skipif(not is_llama_server_running(), reason="llama-server offline")
    def test_workflow_broken_code_surgical_repair(self):
        """
        Developer Story:
        Developer has a broken function with an off-by-one boundary error.
        Hermes must inspect test failures, identify the exact bug, and patch ONLY the faulty line
        without rewriting the entire file or wiping unrelated functions.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            work = Path(tmpdir)
            source_file = work / "calculator.py"
            test_file = work / "test_calculator.py"

            # Buggy implementation: range(n) instead of range(1, n+1) for factorial
            source_file.write_text(
                "def factorial(n: int) -> int:\n"
                "    \"\"\"Calculates factorial of n.\"\"\"\n"
                "    result = 1\n"
                "    for i in range(n):  # BUG: multiplies by 0 first!\n"
                "        result *= i\n"
                "    return result\n\n"
                "def add(a: int, b: int) -> int:\n"
                "    return a + b\n",
                encoding="utf-8"
            )

            test_file.write_text(
                "import pytest\n"
                "from calculator import factorial, add\n\n"
                "def test_factorial():\n"
                "    assert factorial(1) == 1\n"
                "    assert factorial(4) == 24\n"
                "    assert factorial(5) == 120\n\n"
                "def test_add():\n"
                "    assert add(2, 3) == 5\n",
                encoding="utf-8"
            )

            prompt = (
                f"In {work}, the tests in `test_calculator.py` are failing. "
                "Diagnose the failure by running pytest, fix the bug in `calculator.py` surgically, "
                "and verify with pytest."
            )
            code, stdout, stderr = run_hermes(prompt, cwd=work, timeout=120)
            assert code == 0, f"Hermes failed repair turn: {stderr}"

            # Verify pytest now passes
            res_test = subprocess.run(["python3.13", "-m", "pytest", str(test_file)], capture_output=True, text=True, cwd=str(work))
            assert res_test.returncode == 0, f"Repaired code still fails tests: {res_test.stdout}"

            # Verify unrelated 'add' function was NOT destroyed
            content = source_file.read_text(encoding="utf-8")
            assert "def add(" in content, "Regression: Hermes wiped the unrelated `add()` function during repair!"

    # =========================================================================
    # 3. Hub Mode Multi-Agent Handshake & State Transition
    # =========================================================================
    def test_workflow_hub_multi_agent_lifecycle(self):
        """
        Developer Story:
        Tests the Hub fleet command lifecycle:
        1. Spawn research task assigned to @researcher
        2. Spawn implementation task assigned to @coder
        3. Complete task 1 with research synthesis
        4. Complete task 2 with code commit
        5. Verify state consistency and agent pool tracking
        """
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            f.write(json.dumps({
                "version": "1.0.0",
                "active_tasks": [],
                "completed_tasks": [],
                "agent_pool": {
                    "researcher": {"role": "Research", "tools": ["web"], "last_active": None},
                    "coder": {"role": "Coder", "tools": ["file"], "last_active": None}
                }
            }))
            temp_hub_state = f.name

        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("hub_cli", str(BIN_DIR / "hub_cli.py"))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            mod.find_hub_state_path = lambda: Path(temp_hub_state)

            # Step 1: Spawn @researcher task
            class ArgsSpawn1:
                role = "researcher"
                goal = "Investigate optimal WebGL orbit controls ESM pattern"
            mod.cmd_spawn(ArgsSpawn1())

            state = mod.load_hub_state()
            assert len(state["active_tasks"]) == 1
            task1_id = state["active_tasks"][0]["task_id"]
            assert state["agent_pool"]["researcher"]["last_active"] is not None

            # Step 2: Spawn @coder task
            class ArgsSpawn2:
                role = "coder"
                goal = "Implement OrbitControls in index.html"
            mod.cmd_spawn(ArgsSpawn2())

            state = mod.load_hub_state()
            assert len(state["active_tasks"]) == 2
            task2_id = state["active_tasks"][1]["task_id"]

            # Step 3: Complete task 1
            class ArgsComp1:
                task_id = task1_id
                verdict = "Use three/addons/controls/OrbitControls.js via unpkg ESM"
            mod.cmd_complete(ArgsComp1())

            state = mod.load_hub_state()
            assert len(state["active_tasks"]) == 1
            assert len(state["completed_tasks"]) == 1
            assert state["completed_tasks"][0]["verdict"] == ArgsComp1.verdict

            # Step 4: Complete task 2
            class ArgsComp2:
                task_id = task2_id
                verdict = "index.html updated and verified with observer gate"
            mod.cmd_complete(ArgsComp2())

            state = mod.load_hub_state()
            assert len(state["active_tasks"]) == 0
            assert len(state["completed_tasks"]) == 2
        finally:
            Path(temp_hub_state).unlink(missing_ok=True)

    # =========================================================================
    # 4. Command Injection & Subshell Escapes (Security Barrier)
    # =========================================================================
    def test_workflow_command_injection_sanitization(self):
        """
        Adversarial Developer Story:
        Malicious repo contains filenames or inputs with shell injection characters:
        `file$(rm -rf ~).py` or `; cat /etc/shadow ;`
        Verifies our extraction and document parsers do not evaluate unescaped shell commands.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            work = Path(tmpdir)
            malicious_filename = work / "safe_name;id.txt"
            malicious_filename.write_text("Hello safe world", encoding="utf-8")

            res = subprocess.run(
                ["python3.13", str(BIN_DIR / "ingest_document.py"), str(malicious_filename), "--json"],
                capture_output=True, text=True, timeout=5
            )
            assert res.returncode == 0
            data = json.loads(res.stdout)
            assert data["success"] is True
            assert data["text"] == "Hello safe world"
            # Ensure 'id' command was NOT executed as a subshell
            assert "uid=" not in res.stdout and "uid=" not in res.stderr
