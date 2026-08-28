"""
Antigravity Skills Bridge (Milestone U72)
=========================================
Discovers, adapts, and mounts Antigravity CLI runtime skills into the Tier L1 Agent
hierarchy, allowing Hermes bots to leverage Antigravity's high-leverage tooling.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
from hermes_core.skill_router import SkillStub


@dataclass
class AntigravitySkillBridgeResult:
    discovered_skills: List[SkillStub]
    mounted_count: int
    target_tier: str = "L1_AGENT"


class AntigravitySkillsBridge:
    """Discovers Antigravity skills in builtin/custom locations and bridges them."""

    def __init__(self, search_paths: Optional[List[Path]] = None):
        self.search_paths = search_paths or self._default_paths()

    def _default_paths(self) -> List[Path]:
        paths = []
        home = Path.home()
        p1 = home / ".gemini" / "antigravity-cli" / "builtin" / "skills"
        if p1.exists():
            paths.append(p1)
        p2 = home / ".agents" / "skills"
        if p2.exists():
            paths.append(p2)
        return paths

    def discover_skills(self) -> AntigravitySkillBridgeResult:
        stubs: List[SkillStub] = []
        for base in self.search_paths:
            for skill_file in base.rglob("SKILL.md"):
                try:
                    content = skill_file.read_text(encoding="utf-8")
                    name = skill_file.parent.name
                    desc = f"Antigravity Skill: {name}"
                    for line in content.splitlines():
                        if line.startswith("description:"):
                            desc = line.split("description:", 1)[1].strip().strip('"\'')
                            break

                    stub = SkillStub(
                        name=f"agy-{name}",
                        tier="L1_AGENT",
                        description=desc,
                        path=str(skill_file),
                        triggers=[name, f"agy-{name}"],
                        content=content,
                        token_count=len(content.split()),
                    )
                    stubs.append(stub)
                except Exception:
                    continue

        return AntigravitySkillBridgeResult(
            discovered_skills=stubs,
            mounted_count=len(stubs),
            target_tier="L1_AGENT",
        )


def create_antigravity_bridge(search_paths: Optional[List[Path]] = None) -> AntigravitySkillsBridge:
    return AntigravitySkillsBridge(search_paths=search_paths)
