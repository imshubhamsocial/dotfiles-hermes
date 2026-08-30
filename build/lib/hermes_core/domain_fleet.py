"""
Domain Bot Fleet Engine (Milestones U67-U71 & Invariant R5-3)
============================================================
Provides clean-room execution isolation and prompt assembly for specialized domain bots:
  - @architect (U67): Spec-first planner and DAG mapper
  - @coder (U68): TDD code synthesizer
  - @tester (U69): Dynamic invariant tester
  - @researcher (U70): Deep web and Second Brain curator
  - Domain specialists (U71): @domain-code-review, @domain-design, @domain-security, @domain-devops

Enforces Invariant R5-3: Bot Isolation Purity (Each bot loads strictly its own rules and skills).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

from hermes_core.intent_router import BotProfile, create_intent_router
from hermes_core.skill_router import FourTierSkillRouter, create_skill_router
from hermes_core.web_grounding import WebGroundingEngine, create_web_grounding_engine


@dataclass
class BotExecutionState:
    bot_class: str
    display_name: str
    scratchpad_dir: Path
    grounding_context: str = ""
    injected_skill: str = ""
    guardrails: List[str] = field(default_factory=list)
    system_prompt: str = ""
    token_budget: int = 400


class DomainFleetManager:
    """Manages domain bot instantiation with clean-room isolation."""

    def __init__(
        self,
        rules_dir: Optional[Path] = None,
        scratchpad_root: Optional[Path] = None,
    ):
        self.rules_dir = rules_dir or (Path.home() / ".hermes" / "rules" / "bots")
        self.scratchpad_root = scratchpad_root or Path("/dev/shm/hermes_scratchpads")
        self.intent_router = create_intent_router()
        self.skill_router = create_skill_router()
        self.web_grounding = create_web_grounding_engine()
        self.bots: Dict[str, BotProfile] = {}
        self._load_bot_configs()

    def _load_bot_configs(self) -> None:
        if not self.rules_dir.exists():
            return
        for yaml_file in self.rules_dir.glob("*.yaml"):
            try:
                with open(yaml_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                b_class = data.get("bot_class", yaml_file.stem)
                self.bots[b_class] = BotProfile(
                    bot_class=b_class,
                    display_name=data.get("display_name", f"@{b_class}"),
                    description=data.get("description", ""),
                    triggers=data.get("triggers", []),
                    skills_allowed=data.get("skills_allowed", []),
                    web_search_policy=data.get("web_search_policy", "always"),
                    context_ceiling_tok=data.get("context_ceiling_tok", 350),
                    guardrails=data.get("guardrails", []),
                )
            except Exception:
                continue

    def get_bot(self, bot_class: str) -> Optional[BotProfile]:
        return self.bots.get(bot_class)

    def prepare_bot_turn(
        self,
        bot_class: str,
        task_prompt: str,
        session_id: str = "default",
    ) -> BotExecutionState:
        """Prepare isolated execution context obeying Invariant R5-3."""
        profile = self.get_bot(bot_class)
        if not profile:
            profile = self.intent_router.profiles.get(bot_class, self.intent_router.profiles["coder"])

        # 1. Clean-Room Scratchpad
        sp_dir = self.scratchpad_root / session_id / profile.bot_class
        sp_dir.mkdir(parents=True, exist_ok=True)

        # 2. Web Grounding according to bot policy
        grounding = self.web_grounding.ground(
            query=task_prompt,
            policy=profile.web_search_policy,
            trigger_context=profile.bot_class,
            max_tokens=profile.context_ceiling_tok // 2,
        )

        # 3. Single-Skill Routing (filtered strictly by bot's allowed skills)
        skill_res = self.skill_router.route(task_prompt, max_tokens=150)
        injected_skill = ""
        if skill_res.matched and skill_res.skill:
            if skill_res.skill.name in profile.skills_allowed or not profile.skills_allowed:
                injected_skill = skill_res.injected_prompt

        # 4. Assemble clean prompt
        prompt_parts = [
            f"=== ROLE: {profile.display_name} ===",
            profile.description,
            "\n[GUARDRAILS]",
        ]
        for g in profile.guardrails:
            prompt_parts.append(f"- {g}")

        if grounding.markdown_context:
            prompt_parts.append(f"\n{grounding.markdown_context}")

        if injected_skill:
            prompt_parts.append(f"\n{injected_skill}")

        prompt_parts.append(f"\n[TASK]\n{task_prompt}")
        sys_prompt = "\n".join(prompt_parts)

        return BotExecutionState(
            bot_class=profile.bot_class,
            display_name=profile.display_name,
            scratchpad_dir=sp_dir,
            grounding_context=grounding.markdown_context,
            injected_skill=injected_skill,
            guardrails=profile.guardrails,
            system_prompt=sys_prompt,
            token_budget=profile.context_ceiling_tok,
        )


def create_domain_fleet_manager(**kwargs) -> DomainFleetManager:
    return DomainFleetManager(**kwargs)
