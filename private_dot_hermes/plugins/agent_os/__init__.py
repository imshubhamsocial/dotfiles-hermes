"""
Hermes Plugin: agent_os
=======================
Two-Tier Agent OS Standards & Plan.json Decomposition Engine.
"""

from .standards import (
    RuleFile,
    CompiledStandards,
    RuleParser,
    TwoTierStandardsEngine,
    build_two_tier_slot3_injection,
    get_standards_engine,
    reset_standards_engine,
)
from .planner import (
    EngineeringSpec,
    PlanStep,
    Plan,
    SpecFirstPlanner,
    inject_plan_into_slot3,
    enforce_plan_gate_before_edit,
    get_spec_first_planner,
    reset_spec_first_planner,
)

def register(ctx=None):
    """Registers plugin agent_os into Hermes runtime."""
    if not ctx:
        return
    
    if hasattr(ctx, "register_cli_command"):
        def setup_exam(parser):
            parser.description = "Run Hermes Agent OS comprehensive system exam"

        def handle_exam(args):
            import subprocess
            from pathlib import Path
            from hermes_constants import get_hermes_home
            home = get_hermes_home()
            proj_venv = Path.cwd() / ".hermes" / "hermes-agent" / "venv" / "bin" / "pytest"
            venv_pytest = proj_venv if proj_venv.exists() else (home / "hermes-agent" / "venv" / "bin" / "pytest")
            proj_tests = Path.cwd() / ".hermes" / "tests"
            tests_dir = proj_tests if proj_tests.exists() else (home / "tests")
            print("Running Hermes Agent OS System Exam...")
            ret = subprocess.run([str(venv_pytest), str(tests_dir), "-q"]).returncode
            if ret == 0:
                print("✓ All exam checks passed.")
            return ret

        def setup_test(parser):
            parser.description = "Run Hermes Agent OS test suite"

        def handle_test(args):
            import subprocess
            from pathlib import Path
            from hermes_constants import get_hermes_home
            home = get_hermes_home()
            venv_pytest = home / "hermes-agent" / "venv" / "bin" / "pytest"
            tests_dir = home / "tests"
            return subprocess.run([str(venv_pytest), str(tests_dir), "-v"]).returncode

        ctx.register_cli_command("exam", "Run Hermes Agent OS system exam", setup_exam, handle_exam)
        ctx.register_cli_command("test", "Run Hermes Agent OS contract test suite", setup_test, handle_test)

    if hasattr(ctx, "register_command"):
        def slash_exam(raw_args: str) -> str:
            import subprocess
            from pathlib import Path
            from hermes_constants import get_hermes_home
            home = get_hermes_home()
            venv_pytest = home / "hermes-agent" / "venv" / "bin" / "pytest"
            tests_dir = home / "tests"
            res = subprocess.run([str(venv_pytest), str(tests_dir), "-q"], capture_output=True, text=True)
            return res.stdout or res.stderr

        ctx.register_command("exam", slash_exam, "Run system examination", "")

__all__ = [
    "RuleFile",
    "CompiledStandards",
    "RuleParser",
    "TwoTierStandardsEngine",
    "build_two_tier_slot3_injection",
    "get_standards_engine",
    "reset_standards_engine",
    "EngineeringSpec",
    "PlanStep",
    "Plan",
    "SpecFirstPlanner",
    "inject_plan_into_slot3",
    "enforce_plan_gate_before_edit",
    "get_spec_first_planner",
    "reset_spec_first_planner",
    "register",
]
