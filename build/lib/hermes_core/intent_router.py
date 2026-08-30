"""
Intent Router & Bot Class Selector (Milestone U61)
==================================================
Classifies incoming user tasks/prompts and routes them to the appropriate
specialized domain bot class based on ~/.hermes/rules/bot_registry.yaml.

Returns the target bot profile, allowed skills, context limits, and web search policy.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml


@dataclass
class BotProfile:
    bot_class: str
    display_name: str
    description: str
    triggers: List[str]
    skills_allowed: List[str]
    web_search_policy: str
    context_ceiling_tok: int
    guardrails: List[str] = field(default_factory=list)


@dataclass
class IntentRoutingDecision:
    prompt: str
    target_bot: BotProfile
    confidence: float
    matched_triggers: List[str]
    injected_guardrails: str


class IntentRouter:
    """Classifies prompts and selects specialized domain bot instances."""

    def __init__(self, registry_path: Optional[Path] = None):
        self.registry_path = registry_path or self._find_registry_path()
        self.profiles: Dict[str, BotProfile] = {}
        self.default_bot: str = "coder"
        self._load_registry()

    def _find_registry_path(self) -> Path:
        p1 = Path.home() / ".hermes" / "rules" / "bot_registry.yaml"
        if p1.exists():
            return p1
        p2 = Path(os.getcwd()) / ".hermes" / "rules" / "bot_registry.yaml"
        return p2

    def _load_registry(self) -> None:
        if not self.registry_path.exists():
            # Fallback default registry
            self._load_defaults()
            return

        try:
            with open(self.registry_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            self.default_bot = data.get("default_bot", "coder")
            raw_bots = data.get("bots", {})
            for b_class, b_info in raw_bots.items():
                self.profiles[b_class] = BotProfile(
                    bot_class=b_class,
                    display_name=b_info.get("display_name", f"@{b_class}"),
                    description=b_info.get("description", ""),
                    triggers=b_info.get("triggers", []),
                    skills_allowed=b_info.get("skills_allowed", []),
                    web_search_policy=b_info.get("web_search_policy", "always"),
                    context_ceiling_tok=b_info.get("context_ceiling_tok", 350),
                    guardrails=b_info.get("guardrails", []),
                )
        except Exception:
            self._load_defaults()

    def _load_defaults(self) -> None:
        self.default_bot = "coder"
        self.profiles["coder"] = BotProfile(
            bot_class="coder",
            display_name="@coder",
            description="Default code synthesizer",
            triggers=["code", "implement"],
            skills_allowed=["test-driven-development"],
            web_search_policy="before_code",
            context_ceiling_tok=350,
            guardrails=["Adhere to plan.json"],
        )

    def route_intent(self, prompt: str) -> IntentRoutingDecision:
        """Score prompt against registered bot triggers and select best match."""
        # 1. Explicit mention check: @architect, @coder, @tester, etc.
        for b_class, profile in self.profiles.items():
            if f"@{b_class}" in prompt.lower() or profile.display_name.lower() in prompt.lower():
                guardrails_text = self._format_guardrails(profile)
                return IntentRoutingDecision(
                    prompt=prompt,
                    target_bot=profile,
                    confidence=1.0,
                    matched_triggers=[profile.display_name],
                    injected_guardrails=guardrails_text,
                )

        # 2. Trigger phrase matching
        prompt_lower = prompt.lower()
        best_bot = self.default_bot
        best_score = 0
        matched_trigs = []

        for b_class, profile in self.profiles.items():
            score = 0
            current_matched = []
            for trig in profile.triggers:
                # Word boundary match
                pattern = r"\b" + re.escape(trig.lower()) + r"\b"
                matches = re.findall(pattern, prompt_lower)
                if matches:
                    weight = len(trig.split()) * 2  # Longer trigger phrases get higher weight
                    score += weight * len(matches)
                    current_matched.append(trig)

            if score > best_score:
                best_score = score
                best_bot = b_class
                matched_trigs = current_matched

        chosen_profile = self.profiles.get(best_bot, self.profiles[self.default_bot])
        conf = min(1.0, 0.5 + (best_score * 0.1)) if best_score > 0 else 0.5
        guardrails_text = self._format_guardrails(chosen_profile)

        return IntentRoutingDecision(
            prompt=prompt,
            target_bot=chosen_profile,
            confidence=conf,
            matched_triggers=matched_trigs,
            injected_guardrails=guardrails_text,
        )

    def _format_guardrails(self, profile: BotProfile) -> str:
        lines = [f"### [BOT ROLE: {profile.display_name}]", profile.description]
        if profile.guardrails:
            lines.append("Guardrails:")
            for g in profile.guardrails:
                lines.append(f"- {g}")
        return "\n".join(lines)

    def detect_language(self, prompt: str) -> str:
        """Determines programming language from syntax keywords and prompt context."""
        p_lower = prompt.lower()
        if any(k in p_lower for k in ["c++", "cpp", "c++20", "std::", "raii", "unique_ptr", "g++"]):
            return "cpp"
        if any(k in p_lower for k in ["rust", "cargo", "rustc", "borrow checker", "tokio"]):
            return "rust"
        if any(k in p_lower for k in ["three.js", "threejs", "webgl", "canvas", "orbitcontrols", "requestanimationframe"]):
            return "webgl"
        if any(k in p_lower for k in ["python", "pytest", "fastapi", "asyncio", "dataclass", "ruff"]):
            return "python"
        if any(k in p_lower for k in ["javascript", "typescript", "node", "npm", "react"]):
            return "javascript"
        return "python"

    def get_compiler_toolchain(self, language: str) -> Dict[str, str]:
        """Returns deterministic container toolchain commands for the target language."""
        toolchains = {
            "cpp": {
                "compiler": "g++ -std=c++20 -Wall -Wextra -O3",
                "linter": "clang-tidy",
                "debugger": "gdb",
                "verifier": "g++ -std=c++20 -Wall -Wextra -Werror -fsyntax-only",
            },
            "rust": {
                "compiler": "cargo build --release",
                "linter": "cargo clippy",
                "tester": "cargo test",
                "verifier": "cargo check",
            },
            "python": {
                "runtime": "python3.13",
                "linter": "ruff check",
                "formatter": "ruff format",
                "tester": "python3.13 -m pytest",
                "verifier": "python3.13 -m py_compile",
            },
            "webgl": {
                "runtime": "node --experimental-vm-modules",
                "linter": "oxlint",
                "verifier": "python3.13 .hermes/bin/observer_gate.py",
            },
            "javascript": {
                "runtime": "node",
                "linter": "oxlint",
                "verifier": "python3.13 .hermes/bin/observer_gate.py",
            },
        }
        return toolchains.get(language, toolchains["python"])

    def get_canonical_scaffold(self, language: str) -> str:
        """Returns verified minimal AST scaffold (<200 tokens) for the language."""
        scaffolds = {
            "cpp": "// C++20 Canonical RAII Wrapper\n#include <memory>\n#include <concepts>\n\ntemplate<typename T>\nconcept ValidState = requires(T a) { { a.is_valid() } -> std::same_as<bool>; };\n",
            "python": "# Python 3.13 Modern Async Dataclass\nfrom __future__ import annotations\nfrom dataclasses import dataclass, field\nfrom pathlib import Path\nimport asyncio\n",
            "webgl": "<!DOCTYPE html>\n<html>\n<head><meta charset=\"utf-8\"><title>Simulation</title></head>\n<body>\n<canvas id=\"c\"></canvas>\n<script type=\"module\">\nimport * as THREE from 'https://unpkg.com/three@0.128.0/build/three.module.js';\n</script>\n</body>\n</html>\n",
            "rust": "// Rust Idiomatic Safe Module\nuse std::error::Error;\n\npub type Result<T> = std::result::Result<T, Box<dyn Error>>;\n",
        }
        return scaffolds.get(language, scaffolds["python"])


def create_intent_router(registry_path: Optional[Path] = None) -> IntentRouter:
    return IntentRouter(registry_path=registry_path)
