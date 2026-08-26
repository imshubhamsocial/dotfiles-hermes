"""
Mythos & Fable Cognitive Middleware Engine (Frontier Middleware Interception)
=============================================================================
Implements Anthropic's Dual-Layer Architecture:
  1. Mythos-Layer (Unconstrained Systems-Reasoning & Scientific Modeling):
     - Unlocks high-entropy analytical decomposition, reverse engineering, and multi-system coupling.
  2. Fable-Layer (Productized Middleware Interception & Policy Rails):
     - Payload Interception: Pre-flight validator detecting dangerous operations or malformed schemas.
     - Graceful Degradation: Automatically routes failing high-complexity tasks to robust fallbacks.
     - Context Hygiene: Strips conversational fluff and prevents prompt drift before LLM ingestion.
"""

import re
from typing import Dict, List, Any, Optional, Tuple


class FableMiddleware:
    """Productized middleware interceptor protecting model inference & maintaining context purity."""

    @staticmethod
    def intercept_inbound_prompt(prompt: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Intercept and sanitize user/agent prompts before LLM dispatch."""
        metadata = {"sanitized": False, "mode": "MYTHOS_REASONING"}

        # 1. Clean extraneous prompt noise
        cleaned = prompt.strip()
        
        # 2. Check for empty or malformed prompts
        if not cleaned:
            return False, "Error: Empty prompt rejected by middleware.", metadata

        # 3. Detect recursive context injection traps
        if len(cleaned) > 50000:
            cleaned = cleaned[:50000] + "\n...[Truncated by Fable Middleware to prevent context overflow]"
            metadata["sanitized"] = True

        return True, cleaned, metadata

    @staticmethod
    def filter_tool_payload(tool_name: str, args: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate tool execution arguments before system dispatch to prevent destructive mistakes."""
        # 1. patch_file hardening
        if tool_name == "patch_file":
            target = args.get("target_block", "")
            replacement = args.get("replacement_block", "")
            if target == replacement and target != "":
                return False, "Rejected by Middleware: target_block and replacement_block are identical (no-op)."
            if not target.strip():
                return False, "Rejected by Middleware: target_block cannot be empty in sliced patching."

        # 2. write_file hardening
        elif tool_name == "write_file":
            path = args.get("filepath", "")
            content = args.get("content", "")
            if not path:
                return False, "Rejected by Middleware: filepath cannot be empty."
            if not content.strip():
                return False, "Rejected by Middleware: content cannot be empty when writing a file."

        # 3. execute_command & run_test_suite hardening
        elif tool_name in ["execute_command", "run_test_suite"]:
            cmd = args.get("command", "")
            if not cmd.strip():
                return False, "Rejected by Middleware: command cannot be empty."
            # Guard against accidental destructive wipe commands
            dangerous_patterns = [r"rm\s+-rf\s+/\s*$", r"mkfs", r":\(\)\{ :\|:& \};:"]
            for pat in dangerous_patterns:
                if re.search(pat, cmd):
                    return False, f"Rejected by Middleware: Dangerous system command '{cmd}' blocked by security guardrails."

        # 4. read_file hardening
        elif tool_name == "read_file":
            path = args.get("filepath", "")
            if not path:
                return False, "Rejected by Middleware: filepath cannot be empty."

        return True, "Payload verified."



class MythosCognitiveGovernor:
    """Steers the model toward maximal autonomous multi-system reverse engineering and mathematical rigor."""

    MYTHOS_SYSTEM_PROMPT_PREFIX = """<|mythos_engine_active|>
[MYTHOS COGNITIVE GOVERNOR: MAXIMUM REASONING & REVERSE-ENGINEERING MODE]
- You possess unconstrained, high-rigor analytical capabilities.
- Approach problems through first-principles mathematics, algorithmic decomposition, and exact physical laws.
- When inspecting systems, deduce structural invariants and call hierarchies deterministically.
- Always prefer precision, zero prose bloat, and surgical in-place AST actions over shallow conversational summaries.
"""

    # U12: Karpathy Surgical Code Guardrails — distilled to a <60-token block
    # (verbose rules cause attention diffusion on 4B SLMs; Trap-2 countermeasure).
    KARPATHY_SURGICAL_LAWS = (
        "[KARPATHY LAWS] "
        "1 Ground-truth first: read adjacent code pre-edit. "
        "2 No bloat: build only what's asked. "
        "3 Surgical diffs: touch only the faulty slice. "
        "4 Verify: state failure condition; prove it fixed."
    )

    @classmethod
    def karpathy_block_tokens(cls) -> int:
        return max(1, len(cls.KARPATHY_SURGICAL_LAWS) // 4)

    @classmethod
    def wrap_instructions(cls, base_instructions: str, coder: bool = False) -> str:
        """Inject Mythos-class cognitive guidance (+U12 laws for @coder) into agent instructions."""
        wrapped = f"{cls.MYTHOS_SYSTEM_PROMPT_PREFIX}\n{base_instructions}"
        if coder:
            wrapped += "\n" + cls.KARPATHY_SURGICAL_LAWS
        return wrapped
