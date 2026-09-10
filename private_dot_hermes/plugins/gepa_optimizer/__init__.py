"""
Hermes Plugin: gepa_optimizer
=============================
Reflective Pareto prompt and skill evolution engine.
Wires DSPy-based prompt compilation and SkillEvaluator benchmark suite.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from hermes_constants import get_hermes_home
from .hooks.on_session_end import on_session_end


def register(ctx=None):
    """Registers plugin gepa_optimizer into Hermes runtime."""
    if not ctx:
        return True

    # 1. Lifecycle Hook: on_session_end
    if hasattr(ctx, "register_hook"):
        ctx.register_hook("on_session_end", on_session_end)

    # 2. Native CLI command: hermes benchmark skills
    if hasattr(ctx, "register_cli_command"):
        def setup_benchmark(parser):
            parser.description = "Run NVIDIA SkillEvaluator delta benchmarks across developer tasks"
            subparsers = parser.add_subparsers(dest="subcommand", help="Benchmark actions")

            skills_p = subparsers.add_parser("skills", help="Evaluate skill lift against canonical tasks")
            skills_p.add_argument("--json", action="store_true", help="Output results as JSON")

        def handle_benchmark(args):
            subcmd = getattr(args, "subcommand", None) or "skills"
            if subcmd == "skills":
                hermes_home = str(get_hermes_home())
                if hermes_home not in sys.path:
                    sys.path.insert(0, hermes_home)
                from benchmarks.skill_lift.runner import run_full_benchmark

                print("Running NVIDIA SkillEvaluator benchmark suite...")
                report = run_full_benchmark()
                if getattr(args, "json", False):
                    print(json.dumps(report, indent=2))
                else:
                    print(f"\nSkillEvaluator Benchmark Summary:")
                    print(f"  Total Tasks:    {report['total_tasks']}")
                    print(f"  Base Accuracy:  {report['base_accuracy'] * 100:.1f}%")
                    print(f"  Skill Accuracy: {report['skill_accuracy'] * 100:.1f}%")
                    print(f"  Net Skill Lift: +{report['skill_lift_pct']:.1f}%\n")
                    print("  Task Details:")
                    for t in report["tasks"]:
                        base_m = "✓" if t["base_passed"] else "✗"
                        skill_m = "✓" if t["skill_passed"] else "✗"
                        print(f"    - [{t['id']}] Base: {base_m} | Skill: {skill_m} | {t['skill']}")
                return 0
            return 0

        ctx.register_cli_command("benchmark", "Run SkillEvaluator performance benchmarks", setup_benchmark, handle_benchmark)

    # 3. Native Slash command: /benchmark
    if hasattr(ctx, "register_command"):
        def slash_benchmark(raw_args: str) -> str:
            hermes_home = str(get_hermes_home())
            if hermes_home not in sys.path:
                sys.path.insert(0, hermes_home)
            from benchmarks.skill_lift.runner import run_full_benchmark

            report = run_full_benchmark()
            lines = [
                "**SkillEvaluator Delta Benchmark**",
                f"- **Base Accuracy**: `{report['base_accuracy'] * 100:.1f}%`",
                f"- **Skill Accuracy**: `{report['skill_accuracy'] * 100:.1f}%`",
                f"- **Net Skill Lift**: `+{report['skill_lift_pct']:.1f}%`",
                f"- **Tasks Tested**: `{report['total_tasks']}`",
            ]
            return "\n".join(lines)

        ctx.register_command("benchmark", slash_benchmark, "Run skill lift benchmarks", "")

    return True


__all__ = ["on_session_end", "register"]
