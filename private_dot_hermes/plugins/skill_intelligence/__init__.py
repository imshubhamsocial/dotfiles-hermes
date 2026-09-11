"""
Hermes Plugin: skill_intelligence
=================================
Frontier Skill Intelligence OS.
Synthesizes:
1. Gemini 3.8 Thought Signatures: Dynamic task state machine tracking initial decomposition,
   active subgoals, completed milestones, and context drift. Durable storage with RAM hot-mirror.
2. Superpowers Registry (obra/superpowers pattern): Dynamic capability declarations
   and multi-agent capability matching.
3. 4-Block XML Contract Validator: Ensures all procedural skills conform to the frontier
   model schema (<instructions>, <context>, <task>, <output_requirements>).
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# =============================================================================
# Subsystem 1: Gemini 3.8 Thought Signatures
# =============================================================================
class ThoughtSignature:
    def __init__(
        self,
        task_id: str,
        initial_goal: str,
        initial_decomposition: List[str],
        created_at: Optional[str] = None,
        completed_steps: Optional[List[str]] = None,
        active_step: Optional[str] = None,
        confidence: float = 0.90,
        context_drift_score: float = 0.0,
    ):
        self.task_id = task_id
        self.initial_goal = initial_goal
        self.initial_decomposition = initial_decomposition
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.completed_steps = completed_steps or []
        self.active_step = active_step or (initial_decomposition[0] if initial_decomposition else "Initial execution")
        self.confidence = confidence
        self.context_drift_score = context_drift_score
        self.turn_count = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "initial_goal": self.initial_goal,
            "initial_decomposition": self.initial_decomposition,
            "created_at": self.created_at,
            "completed_steps": self.completed_steps,
            "active_step": self.active_step,
            "confidence": round(self.confidence, 3),
            "context_drift_score": round(self.context_drift_score, 3),
            "turn_count": self.turn_count,
        }


class ThoughtSignatureEngine:
    """Manages creation, updates, and drift monitoring for long-horizon tasks."""

    def __init__(self, storage_dir: Optional[Path] = None):
        if storage_dir:
            self.storage_dir = storage_dir
            self.hot_dir = None
        else:
            hermes_home = os.environ.get("HERMES_HOME")
            base = Path(hermes_home) if hermes_home else Path.home() / ".hermes"
            self.storage_dir = base / "cache" / "thought_signatures"
            shm = Path("/dev/shm/thought_signatures")
            self.hot_dir = shm if shm.parent.exists() else None

        self.storage_dir.mkdir(parents=True, exist_ok=True)
        if self.hot_dir:
            try:
                self.hot_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                self.hot_dir = None

        self.active_signature: Optional[ThoughtSignature] = None
        self._load_latest_signature()

    def _load_latest_signature(self):
        # 1. Check durable storage first
        sig_files = sorted(self.storage_dir.glob("*.json"), key=os.path.getmtime, reverse=True)
        # 2. If durable empty, check RAM hot cache mirror
        if not sig_files and self.hot_dir:
            sig_files = sorted(self.hot_dir.glob("*.json"), key=os.path.getmtime, reverse=True)

        if sig_files:
            try:
                data = json.loads(sig_files[0].read_text(encoding="utf-8"))
                self.active_signature = ThoughtSignature(
                    task_id=data["task_id"],
                    initial_goal=data.get("initial_goal", ""),
                    initial_decomposition=data.get("initial_decomposition", []),
                    created_at=data.get("created_at"),
                    completed_steps=data.get("completed_steps", []),
                    active_step=data.get("active_step"),
                    confidence=data.get("confidence", 0.9),
                    context_drift_score=data.get("context_drift_score", 0.0),
                )
                # Ensure copied to durable storage if loaded from hot_dir
                durable_path = self.storage_dir / f"{data['task_id']}.json"
                if not durable_path.exists():
                    durable_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            except Exception:
                pass

    def create_signature(self, task_id: str, goal: str, steps: List[str]) -> ThoughtSignature:
        """Initializes a new thought signature for an incoming task."""
        sig = ThoughtSignature(
            task_id=task_id,
            initial_goal=goal,
            initial_decomposition=steps,
        )
        self.active_signature = sig
        self._persist_signature(sig)
        return sig

    def update_step(self, completed_step: str, next_step: Optional[str] = None) -> ThoughtSignature:
        """Marks a step as completed and transitions to the next step."""
        if not self.active_signature:
            self.create_signature("default_task", "Default Task", [completed_step])

        sig = self.active_signature
        if completed_step not in sig.completed_steps:
            sig.completed_steps.append(completed_step)

        if next_step:
            sig.active_step = next_step
        else:
            # Pick next from initial decomposition
            remaining = [s for s in sig.initial_decomposition if s not in sig.completed_steps]
            sig.active_step = remaining[0] if remaining else "Task Finalization"

        sig.turn_count += 1
        self._persist_signature(sig)
        return sig

    def evaluate_drift(self, current_turn_content: str) -> float:
        """
        Calculates context drift score between current turn content and initial goal.
        Score: 0.0 = perfect alignment; > 0.6 = drift warning.
        """
        if not self.active_signature or not self.active_signature.initial_goal:
            return 0.0

        goal_words = set(re.findall(r"\w+", self.active_signature.initial_goal.lower()))
        turn_words = set(re.findall(r"\w+", current_turn_content.lower()))

        if not goal_words or not turn_words:
            return 0.0

        # Jaccard semantic distance
        intersection = len(goal_words & turn_words)
        union = len(goal_words | turn_words)
        similarity = (intersection / union) if union > 0 else 1.0

        drift = max(0.0, min(1.0, 1.0 - similarity))
        self.active_signature.context_drift_score = drift
        self._persist_signature(self.active_signature)
        return drift

    def _persist_signature(self, sig: ThoughtSignature):
        content = json.dumps(sig.to_dict(), indent=2)
        # Durable disk write
        path = self.storage_dir / f"{sig.task_id}.json"
        path.write_text(content, encoding="utf-8")
        # RAM hot mirror
        if self.hot_dir:
            try:
                (self.hot_dir / f"{sig.task_id}.json").write_text(content, encoding="utf-8")
            except Exception:
                pass


# =============================================================================
# Subsystem 2: Superpowers Capability Registry (obra/superpowers pattern)
# =============================================================================
class SuperpowersRegistry:
    """Registry of domain superpower capabilities and automated trigger routing."""

    DEFAULT_SUPERPOWERS = {
        "security_audit": {
            "name": "Security Audit & Vulnerability Elimination",
            "triggers": ["security", "vulnerability", "cve", "audit", "exploit", "sanitize"],
            "capabilities": ["AST AST-grep static analysis", "Sink-source dataflow trace", "Blast radius calculation"],
            "skill_ref": "engineering/security-audit/SKILL.md",
        },
        "secret_detection": {
            "name": "Shannon Entropy Credential Protection",
            "triggers": ["secret", "credential", "api key", "token leak", "password"],
            "capabilities": ["Shannon entropy calculation", "Regex signature matching", "Automatic credential redaction"],
            "skill_ref": "engineering/secret-detection/SKILL.md",
        },
        "threat_model": {
            "name": "STRIDE Architectural Threat Modeling",
            "triggers": ["threat model", "stride", "attack surface", "repudiation"],
            "capabilities": ["Multi-agent trust boundary audit", "Cryptographic chain verification", "Mitigation gating"],
            "skill_ref": "engineering/threat-model/SKILL.md",
        },
        "code_refactor": {
            "name": "Spec-Driven Code Modernization",
            "triggers": ["refactor", "modernize", "clean up", "redesign", "idiomatic"],
            "capabilities": ["Type contract enforcement", "Modern language idioms", "Zero-regression diffing"],
            "skill_ref": "software-development/refactoring/SKILL.md",
        },
        "spec_driven": {
            "name": "Spec-Driven Architecture Decomposition",
            "triggers": ["plan", "design", "architect", "spec", "blueprint", "schema"],
            "capabilities": ["DAG topological sorting", "Interface typing", "Invariants formulation"],
            "skill_ref": "engineering/spec-driven-development/SKILL.md",
        },
    }

    def __init__(self, registry_file: Optional[Path] = None):
        if registry_file:
            self.registry_file = registry_file
        else:
            hermes_home = os.environ.get("HERMES_HOME")
            base = Path(hermes_home) if hermes_home else Path.home() / ".hermes"
            self.registry_file = base / "rules" / "superpowers_registry.json"

        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        self.superpowers = dict(self.DEFAULT_SUPERPOWERS)
        self._load_registry()

    def _load_registry(self):
        if self.registry_file.exists():
            try:
                data = json.loads(self.registry_file.read_text(encoding="utf-8"))
                self.superpowers.update(data)
            except Exception:
                pass
        else:
            self._save_registry()

    def _save_registry(self):
        self.registry_file.write_text(json.dumps(self.superpowers, indent=2), encoding="utf-8")

    def match(self, query: str) -> List[Dict[str, Any]]:
        """Matches a user or agent prompt against superpower triggers."""
        q_lower = query.lower()
        query_words = set(re.findall(r"\w+", q_lower))
        matches = []

        for sp_id, data in self.superpowers.items():
            triggers = data.get("triggers", [])
            score = 0
            for t in triggers:
                if t in q_lower:
                    score += 2
                elif any(w in query_words for w in t.split()):
                    score += 1

            if score > 0:
                matches.append({
                    "id": sp_id,
                    "name": data.get("name", sp_id),
                    "score": score,
                    "skill_ref": data.get("skill_ref"),
                    "capabilities": data.get("capabilities", []),
                })

        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches

    def list_all(self) -> List[Dict[str, Any]]:
        return [{"id": k, **v} for k, v in self.superpowers.items()]


# =============================================================================
# Subsystem 3: 4-Block XML Contract Validator
# =============================================================================
class XMLContractValidator:
    """Validates that procedural skills conform to the 4-block XML standard."""

    MANDATORY_TAGS = ["instructions", "context", "task", "output_requirements"]

    @classmethod
    def validate_skill_text(cls, text: str) -> Tuple[bool, List[str]]:
        """Validates skill text against 4-block XML specification."""
        missing = []
        for tag in cls.MANDATORY_TAGS:
            open_tag = f"<{tag}>"
            close_tag = f"</{tag}>"
            if open_tag not in text or close_tag not in text:
                missing.append(tag)

        return len(missing) == 0, missing

    @classmethod
    def validate_skill_file(cls, path: str | Path) -> Dict[str, Any]:
        p = Path(path)
        if not p.exists() or not p.is_file():
            return {"file": str(path), "valid": False, "error": "File not found"}

        content = p.read_text(encoding="utf-8", errors="ignore")
        valid, missing = cls.validate_skill_text(content)
        return {
            "file": str(path),
            "valid": valid,
            "missing_blocks": missing,
            "char_count": len(content),
            "estimated_tokens": len(content) // 4,
        }


_GLOBAL_THOUGHT_ENGINE: Optional[ThoughtSignatureEngine] = None
_GLOBAL_SUPERPOWERS: Optional[SuperpowersRegistry] = None


def get_thought_engine() -> ThoughtSignatureEngine:
    global _GLOBAL_THOUGHT_ENGINE
    if _GLOBAL_THOUGHT_ENGINE is None:
        _GLOBAL_THOUGHT_ENGINE = ThoughtSignatureEngine()
    return _GLOBAL_THOUGHT_ENGINE


def get_superpowers() -> SuperpowersRegistry:
    global _GLOBAL_SUPERPOWERS
    if _GLOBAL_SUPERPOWERS is None:
        _GLOBAL_SUPERPOWERS = SuperpowersRegistry()
    return _GLOBAL_SUPERPOWERS


# =============================================================================
# Subsystem 4: Dynamic Tool Dependency Retrieval (DTDR)
# =============================================================================
class DynamicToolRetriever:
    """Indexes tools and retrieves top-k matching schemas dynamically per turn."""

    DEFAULT_TOOL_CATALOG = [
        {
            "name": "search_replace",
            "category": "editing",
            "description": "Search and replace a unique code block in a file with unified diff emission.",
            "keywords": ["replace", "edit", "patch", "modify", "search", "update", "diff"],
            "parameters": {"file_path": "str", "search_block": "str", "replace_block": "str"},
        },
        {
            "name": "run_code_action",
            "category": "execution",
            "description": "Execute sandboxed Python script (smolagents Code-as-Action) in bubblewrap.",
            "keywords": ["python", "script", "calculate", "run", "execute", "compute", "action"],
            "parameters": {"code": "str"},
        },
        {
            "name": "web_extract",
            "category": "web",
            "description": "Extract clean markdown from web URLs using Crawl4AI.",
            "keywords": ["url", "web", "http", "browse", "scrape", "doc", "internet"],
            "parameters": {"url": "str", "word_limit": "int"},
        },
        {
            "name": "ast_search",
            "category": "search",
            "description": "Structural AST grep pattern search across codebase.",
            "keywords": ["ast", "tree-sitter", "symbol", "pattern", "class", "function", "grep"],
            "parameters": {"pattern": "str", "code": "str", "lang": "str"},
        },
        {
            "name": "read_file",
            "category": "filesystem",
            "description": "Read file contents from local filesystem.",
            "keywords": ["read", "view", "cat", "open", "file", "inspect"],
            "parameters": {"path": "str"},
        },
        {
            "name": "run_command",
            "category": "terminal",
            "description": "Execute non-destructive shell command in terminal.",
            "keywords": ["bash", "shell", "command", "terminal", "exec", "sh"],
            "parameters": {"command": "str"},
        },
    ]

    def __init__(self, catalog: Optional[List[Dict[str, Any]]] = None):
        self.catalog = catalog or list(self.DEFAULT_TOOL_CATALOG)

    def find_tools(self, task_query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Scores and returns top-k tools matching the task query."""
        q_lower = task_query.lower()
        q_words = set(re.findall(r"\w+", q_lower))

        scored = []
        for tool in self.catalog:
            score = 0.0
            if tool["name"] in q_lower:
                score += 3.0
            if tool.get("category", "") in q_lower:
                score += 2.0
            for kw in tool.get("keywords", []):
                if kw in q_words:
                    score += 1.5
                elif kw in q_lower:
                    score += 0.8
            desc_words = set(re.findall(r"\w+", tool.get("description", "").lower()))
            overlap = len(q_words & desc_words)
            score += overlap * 0.5
            scored.append((score, tool))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [t for _, t in scored[:top_k]]

    def format_prompt_injection(self, tools: List[Dict[str, Any]]) -> str:
        """Formats concise tool injection block under 250 tokens."""
        lines = ["<dynamic_tools>"]
        for t in tools:
            param_str = ", ".join(f"{k}: {v}" for k, v in t.get("parameters", {}).items())
            lines.append(f"  <tool name=\"{t['name']}\" args=\"({param_str})\">{t['description']}</tool>")
        lines.append("</dynamic_tools>")
        return "\n".join(lines)


# =============================================================================
# Subsystem 5: Agent2Agent (A2A) Protocols & Typed Handoffs
# =============================================================================
class Agent2AgentProtocol:
    """Machine-to-machine Agent Cards and typed role handoffs."""

    ROLE_CARDS = {
        "architect": {
            "role": "architect",
            "description": "System architecture, requirement decomposition, and test specification generator.",
            "allowed_tools": ["read_file", "ast_search", "web_extract"],
            "output_contract": "SPEC_HANDOFF",
        },
        "coder": {
            "role": "coder",
            "description": "Implementation engineer producing minimal surgical code patches.",
            "allowed_tools": ["read_file", "search_replace", "run_code_action", "ast_search"],
            "output_contract": "PATCH_HANDOFF",
        },
        "tester": {
            "role": "tester",
            "description": "Verification engineer executing tests and invariant regression audits.",
            "allowed_tools": ["read_file", "run_command", "ast_search"],
            "output_contract": "VERDICT_HANDOFF",
        },
    }

    @classmethod
    def get_agent_card(cls, role: str) -> Optional[Dict[str, Any]]:
        return cls.ROLE_CARDS.get(role.lower())

    @staticmethod
    def create_handoff(source_role: str, target_role: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a typed machine-to-machine handoff message."""
        return {
            "protocol": "A2A/1.0",
            "handoff_id": f"A2A-{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_role": source_role.lower(),
            "target_role": target_role.lower(),
            "contract_type": f"{source_role.upper()}_TO_{target_role.upper()}",
            "payload": payload,
        }

    @classmethod
    def validate_handoff(cls, handoff: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        if handoff.get("protocol") != "A2A/1.0":
            return False, "Invalid protocol version"
        if not handoff.get("source_role") or not handoff.get("target_role"):
            return False, "Missing source or target role"
        if not handoff.get("payload"):
            return False, "Handoff payload cannot be empty"
        return True, None


_GLOBAL_TOOL_RETRIEVER: Optional[DynamicToolRetriever] = None


def get_tool_retriever() -> DynamicToolRetriever:
    global _GLOBAL_TOOL_RETRIEVER
    if _GLOBAL_TOOL_RETRIEVER is None:
        _GLOBAL_TOOL_RETRIEVER = DynamicToolRetriever()
    return _GLOBAL_TOOL_RETRIEVER


def register(ctx=None):
    """Registers skill_intelligence plugin into Hermes runtime."""
    if not ctx:
        return True

    thought_engine = get_thought_engine()
    superpowers = get_superpowers()

    # 1. Register CLI Subcommands
    if hasattr(ctx, "register_cli_command"):
        # hermes thought status / init / step
        def setup_thought(parser):
            parser.description = "Inspect and update Gemini 3.8 Thought Signatures"
            sub = parser.add_subparsers(dest="thought_cmd")
            sub.add_parser("status", help="Show active thought signature and drift metrics")

        def handle_thought(args):
            sig = thought_engine.active_signature
            if not sig:
                print("No active thought signature found in storage cache.")
            else:
                d = sig.to_dict()
                print("Gemini 3.8 Thought Signature (Anti-Drift State Machine):")
                print(f"  Task ID:          {d['task_id']}")
                print(f"  Initial Goal:     {d['initial_goal']}")
                print(f"  Active Step:      {d['active_step']}")
                print(f"  Completed Steps:  {len(d['completed_steps'])}/{len(d['initial_decomposition'])} ({', '.join(d['completed_steps']) if d['completed_steps'] else 'None'})")
                print(f"  Confidence:       {d['confidence']}")
                drift_label = "CRITICAL DRIFT ⚠" if d['context_drift_score'] > 0.6 else "ALIGNED ✓"
                print(f"  Context Drift:    {d['context_drift_score']} ({drift_label})")
            return 0

        ctx.register_cli_command("thought", "Inspect Gemini 3.8 Thought Signatures", setup_thought, handle_thought)

        # hermes superpowers [list]
        def setup_sp(parser):
            parser.description = "Inspect Superpowers capability registry"
            parser.add_argument("action", nargs="?", default="list", choices=["list", "status"], help="Action to perform (default: list)")

        def handle_sp(args):
            all_sp = superpowers.list_all()
            print("Superpowers Capability Registry (obra/superpowers pattern):")
            for sp in all_sp:
                print(f"  [{sp['id']}] {sp['name']}")
                print(f"    Triggers: {', '.join(sp['triggers'])}")
                print(f"    Skill:    {sp['skill_ref']}")
                print(f"    Capabilities: {', '.join(sp['capabilities'])}")
            return 0

        ctx.register_cli_command("superpowers", "List active agent superpowers and capability triggers", setup_sp, handle_sp)

        # hermes skills validate-xml <path>
        def setup_xml(parser):
            parser.description = "Validate skill against 4-block XML contract specification"
            parser.add_argument("path", help="Path to SKILL.md file")

        def handle_xml(args):
            res = XMLContractValidator.validate_skill_file(args.path)
            if res["valid"]:
                print(f"✓ 4-Block XML Contract Valid: '{args.path}' ({res['estimated_tokens']} tok)")
                return 0
            else:
                print(f"✗ XML Contract Violation in '{args.path}': Missing blocks: {res['missing_blocks']}")
                return 1

        ctx.register_cli_command("skills-validate-xml", "Validate skill against 4-block XML contract", setup_xml, handle_xml)

    # 2. Register Slash Commands
    if hasattr(ctx, "register_command"):
        def slash_thought(raw_args: str) -> str:
            sig = thought_engine.active_signature
            if not sig:
                return "No active thought signature."
            d = sig.to_dict()
            return (
                f"**Gemini 3.8 Thought Signature**\n"
                f"- **Goal**: {d['initial_goal']}\n"
                f"- **Active Step**: {d['active_step']}\n"
                f"- **Completed**: {len(d['completed_steps'])} steps\n"
                f"- **Drift**: {d['context_drift_score']}"
            )

        def slash_superpowers(raw_args: str) -> str:
            all_sp = superpowers.list_all()
            lines = ["**Active Superpowers**:"]
            for s in all_sp:
                lines.append(f"- **{s['name']}** (`{s['id']}`): {s['skill_ref']}")
            return "\n".join(lines)

        ctx.register_command("thought", slash_thought, "Show active thought signature", "")
        ctx.register_command("superpowers", slash_superpowers, "List active superpowers", "")

    # 3. Lifecycle Hooks
    if hasattr(ctx, "register_hook"):
        def thought_pre_turn_hook(**kwargs):
            """Injects active step and drift guard into prompt prefix."""
            sig = thought_engine.active_signature
            if sig:
                snippet = f"[Thought Signature] Active: '{sig.active_step}' | Drift: {sig.context_drift_score}"
                return {"action": "continue", "injected_context": snippet}
            return {"action": "continue"}

        ctx.register_hook("pre_turn", thought_pre_turn_hook)

    return True


__all__ = [
    "ThoughtSignature",
    "ThoughtSignatureEngine",
    "SuperpowersRegistry",
    "XMLContractValidator",
    "DynamicToolRetriever",
    "Agent2AgentProtocol",
    "get_thought_engine",
    "get_superpowers",
    "get_tool_retriever",
    "register",
]
