"""
Pluggable Skills & Project Grader Protocol Engine (Frontier Modularity)
======================================================================
Implements Pluggable Project Graders and Dynamic Skills:
  1. Base Global Skills: Universal AST search, multi-file refactoring, safe execution.
  2. Project-Specific Pluggable Graders (e.g. Playwright TDD, Pytest, Cargo, WebGL Assertions):
     - Discovered dynamically from `.hermes/graders/` or project config.
     - Automatically executed by @tester without hardcoding benchmark paths in core engine.
  3. Skill Registry & Dynamic Ingestion:
     - Preloads project-specific guidelines without polluting base agent system prompts.
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from pydantic import BaseModel, Field

DEFAULT_WORKSPACE = Path("/dev/shm/hermes_workspace")


class ProjectGrader(BaseModel):
    name: str
    description: str
    command: str
    target_file: Optional[str] = None
    timeout_sec: int = 60
    priority: int = 500  # Tier 1=1000 (Base), Tier 2=500 (Project), Tier 3=100 (Ephemeral)
    env_vars: Dict[str, str] = Field(default_factory=dict)

    def execute(self, workspace_root: Optional[str] = None) -> Tuple[bool, str]:
        """Execute pluggable grader command inside isolated container environment."""
        ws = Path(workspace_root) if workspace_root else DEFAULT_WORKSPACE
        env = os.environ.copy()
        env.update(self.env_vars)

        try:
            res = subprocess.run(
                ["distrobox-enter", "-n", "ws-ai", "--", "bash", "-c", self.command],
                cwd=str(ws) if ws.exists() else ".",
                capture_output=True,
                text=True,
                timeout=self.timeout_sec,
                env=env
            )
            out = (res.stdout + res.stderr).strip()
            return res.returncode == 0, out
        except subprocess.TimeoutExpired:
            return False, f"Grader '{self.name}' timed out after {self.timeout_sec}s."
        except Exception as e:
            return False, f"Error executing grader '{self.name}': {str(e)}"


class SkillMetadata(BaseModel):
    name: str
    tier: int = 2  # 1: Base Immutable, 2: Imported Project Skill, 3: Ephemeral User Override
    priority: int = 500
    description: str
    instructions: str = ""
    is_immutable: bool = False


class PluggableSkillRegistry:
    """Manages 3-Tier Skill Resolution with Strict Precedence:
    Tier 1 (Priority 1000): Base Immutable Core Rules & Primitives (Cannot be overridden)
    Tier 2 (Priority 500):  Imported Project Skills & Domain Graders (Pluggable)
    Tier 3 (Priority 100):  Ephemeral User Overrides & Scratch Prompts (Run-scoped)
    """

    @classmethod
    def discover_project_graders(cls, workspace_root: Optional[str] = None) -> Dict[str, ProjectGrader]:
        """Discover pluggable test graders from project workspace sorted by priority."""
        ws = Path(workspace_root) if workspace_root else DEFAULT_WORKSPACE
        graders: Dict[str, ProjectGrader] = {}

        # 1. Check for explicit project graders.json
        grader_cfg = ws / "graders.json"
        if grader_cfg.exists():
            try:
                data = json.loads(grader_cfg.read_text(encoding="utf-8"))
                for item in data.get("graders", []):
                    g = ProjectGrader(**item)
                    graders[g.name] = g
            except Exception:
                pass

        # 2. Check for standard test harness pro if in Simulation workspace (Priority 800)
        sim_harness = Path("/var/home/imshubhamsocial/Projects/Workspace/Personal/LLMs/Tests/Simulation/tests/test_harness_pro.py")
        if sim_harness.exists():
            graders["simulation_playwright_grader"] = ProjectGrader(
                name="simulation_playwright_grader",
                description="Deterministic Playwright DOM & WebGL Physics Invariant Grader",
                command=f"python3 {sim_harness} build_preview.html",
                target_file="build_preview.html",
                timeout_sec=45,
                priority=800
            )

        # 3. Default fallback: Pytest grader (Priority 100)
        graders["pytest_default"] = ProjectGrader(
            name="pytest_default",
            description="Default Python pytest runner",
            command="pytest",
            timeout_sec=60,
            priority=100
        )

        return graders

    @classmethod
    def get_highest_priority_grader(cls, workspace_root: Optional[str] = None) -> Optional[ProjectGrader]:
        """Resolve active grader strictly using priority ordering."""
        graders = cls.discover_project_graders(workspace_root)
        if not graders:
            return None
        # Sort by priority descending
        sorted_graders = sorted(graders.values(), key=lambda g: g.priority, reverse=True)
        return sorted_graders[0]

    @classmethod
    def run_active_grader(cls, grader_name: Optional[str] = None, workspace_root: Optional[str] = None) -> str:
        """Run requested grader or highest-priority discovered grader."""
        graders = cls.discover_project_graders(workspace_root)
        if not graders:
            return "No pluggable project graders registered."

        if grader_name and grader_name in graders:
            target_g = graders[grader_name]
        else:
            target_g = cls.get_highest_priority_grader(workspace_root)

        if not target_g:
            return "Error: Could not resolve a valid project grader."

        passed, trace = target_g.execute(workspace_root)
        status_str = "PASS ✅" if passed else "FAIL ❌"
        return f"=== PLUGGABLE GRADER: {target_g.name} (Priority {target_g.priority}) [{status_str}] ===\n{trace[:3000]}"

