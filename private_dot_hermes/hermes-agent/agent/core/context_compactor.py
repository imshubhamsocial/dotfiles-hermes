"""
U45: Active Context Compactor Gate
===================================
Monitors active trajectory token volume during multi-turn sessions.
Automatically compacts stale turns into concise semantic summaries when
active history approaches >= 4,000 tokens, while preserving active plan
and diff states verbatim.

Integrates with:
  - token_engine.DifferentialStateCompactor (existing differential compaction)
  - token_engine.GoalAnchor (immutable goal anchor pinned at user-turn head)
  - token_engine.EphemeralToolBuffer (RAMdisk tool streams)
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from .token_engine import (
        DifferentialStateCompactor,
        GoalAnchor,
        EphemeralToolBuffer,
        estimate_tokens,
        KEEP_RECENT_TURNS,
        PLAN_PATH,
        RAMDISK,
    )
except ImportError:
    from token_engine import (
        DifferentialStateCompactor,
        GoalAnchor,
        EphemeralToolBuffer,
        estimate_tokens,
        KEEP_RECENT_TURNS,
        PLAN_PATH,
        RAMDISK,
    )


# =============================================================================
# CONFIGURATION
# =============================================================================

COMPACTION_THRESHOLD_TOKENS = 4000  # Trigger compaction at >= 4000 tokens
TARGET_TOKENS_AFTER_COMPACTION = 2000  # Target ~50% reduction
AUTO_COMPACTION_CEILING_80PCT = 52428  # Auto-trigger compaction at 80% of 65,536 context ceiling
PRESERVE_RECENT_TURNS = 4  # Always keep last N turns verbatim
PRESERVE_PLAN_STATE = True  # Always preserve .hermes/plan.json content verbatim
PRESERVE_ACTIVE_DIFFS = True  # Always preserve active diff/patch states verbatim

# Summary generation templates
SUMMARY_TEMPLATE = """[COMPACTED TURN {turn_index}]
Role: {role}
Summary: {summary}
Tokens Saved: {tokens_saved}"""


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class TurnSummary:
    """Summary of a compacted turn."""
    turn_index: int
    role: str
    original_tokens: int
    summary: str
    summary_tokens: int
    preserved_verbatim: bool = False  # True for plan/diff turns


@dataclass
class CompactionResult:
    """Result of a compaction operation."""
    triggered: bool
    original_token_count: int
    compacted_token_count: int
    turns_compacted: int
    turns_preserved: int
    summaries: List[TurnSummary] = field(default_factory=list)
    compaction_ratio: float = 1.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class ActivePlanState:
    """Active plan and diff state that must be preserved verbatim."""
    plan_json: Optional[Dict[str, Any]] = None
    active_diffs: List[str] = field(default_factory=list)
    current_target: str = ""
    constraints: List[str] = field(default_factory=list)
    
    @classmethod
    def load(cls) -> "ActivePlanState":
        """Load from .hermes/plan.json and any active diff markers."""
        plan_data = {}
        try:
            if PLAN_PATH.exists():
                plan_data = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
        
        return cls(
            plan_json=plan_data,
            active_diffs=[],  # Could be populated from session state
            current_target=plan_data.get("current_target", ""),
            constraints=plan_data.get("constraints", [])
        )
    
    def format_verbatim_block(self) -> str:
        """Format plan state as verbatim block for preservation."""
        if not self.plan_json:
            return ""
        
        lines = ["<|ACTIVE_PLAN_STATE|>"]
        lines.append(f"TARGET: {self.current_target}")
        if self.constraints:
            lines.append("CONSTRAINTS:")
            for c in self.constraints:
                lines.append(f"  - {c}")
        if self.active_diffs:
            lines.append("ACTIVE DIFFS:")
            for d in self.active_diffs:
                lines.append(f"  {d}")
        lines.append("</|ACTIVE_PLAN_STATE|>")
        return "\n".join(lines)


# =============================================================================
# SEMANTIC SUMMARIZER
# =============================================================================

class SemanticSummarizer:
    """
    Generates concise semantic summaries of conversation turns.
    Uses heuristic extraction (no external LLM call for speed).
    """
    
    # Keywords that indicate important content to preserve
    IMPORTANCE_KEYWORDS = {
        "error", "fail", "exception", "traceback", "bug", "fix", "patch",
        "verify", "test", "pass", "verified", "failed", "success",
        "plan", "target", "milestone", "constraint", "requirement",
        "diff", "change", "modify", "update", "refactor",
        "security", "vulnerability", "critical", "important",
        "observer_gate", "ast", "type", "syntax", "import"
    }
    
    def __init__(self, max_summary_tokens: int = 100):
        self.max_summary_tokens = max_summary_tokens
    
    def summarize_assistant_turn(self, content: str, tool_calls: Optional[List[Dict]] = None) -> str:
        """Summarize an assistant turn (may include tool calls)."""
        parts = []
        
        # Tool calls are high priority
        if tool_calls:
            tool_names = [tc.get("function", {}).get("name", "unknown") for tc in tool_calls[:3]]
            parts.append(f"Tools: {', '.join(tool_names)}")
        
        # Extract key sentences from content
        sentences = self._extract_key_sentences(content)
        if sentences:
            parts.append(" ".join(sentences[:2]))
        
        summary = "; ".join(parts) if parts else "Assistant reasoning turn"
        return self._truncate_to_tokens(summary)
    
    def summarize_user_turn(self, content: str) -> str:
        """Summarize a user turn (task instructions, feedback)."""
        # User turns often contain the task - preserve more aggressively
        sentences = self._extract_key_sentences(content)
        if sentences:
            summary = " ".join(sentences[:3])
        else:
            summary = content[:200]
        return self._truncate_to_tokens(summary)
    
    def summarize_tool_turn(self, content: str, tool_name: str = "") -> str:
        """Summarize a tool result turn."""
        # Tool results: preserve errors/failures verbatim, summarize successes
        content_lower = content.lower()
        
        # Check for failure indicators
        if any(kw in content_lower for kw in ["error", "fail", "exception", "traceback", "failed"]):
            # Preserve failure context more fully
            return self._truncate_to_tokens(f"[{tool_name}] FAILURE: {content}", self.max_summary_tokens * 2)
        
        # Success: brief summary
        if "pass" in content_lower or "verified" in content_lower or "success" in content_lower:
            return f"[{tool_name}] PASS/VERIFIED"
        
        # Generic tool result
        lines = content.splitlines()
        key_lines = [l for l in lines if any(kw in l.lower() for kw in self.IMPORTANCE_KEYWORDS)]
        if key_lines:
            return self._truncate_to_tokens(f"[{tool_name}] " + " | ".join(key_lines[:2]))
        
        return f"[{tool_name}] Result: {len(content)} chars"
    
    def _extract_key_sentences(self, text: str) -> List[str]:
        """Extract sentences containing importance keywords."""
        # Simple sentence splitting
        sentences = [s.strip() for s in text.replace('\n', ' ').split('.') if s.strip()]
        key_sentences = []
        for sent in sentences:
            sent_lower = sent.lower()
            if any(kw in sent_lower for kw in self.IMPORTANCE_KEYWORDS):
                key_sentences.append(sent)
        return key_sentences
    
    def _truncate_to_tokens(self, text: str, max_tokens: Optional[int] = None) -> str:
        """Truncate text to approximate token limit."""
        max_t = max_tokens or self.max_summary_tokens
        max_chars = max_t * 4  # 4 chars/token heuristic
        if len(text) <= max_chars:
            return text
        return text[:max_chars - 3] + "..."


# =============================================================================
# CONTEXT COMPACTOR GATE
# =============================================================================

class ContextCompactorGate:
    """
    Active context compactor gate that monitors token volume and triggers
    compaction when threshold is reached.
    
    Preserves:
    - GoalAnchor (immutable, pinned at user-turn head)
    - Active plan state (.hermes/plan.json) verbatim
    - Active diffs/patches verbatim
    - Most recent N turns verbatim
    """
    
    def __init__(
        self,
        threshold_tokens: int = COMPACTION_THRESHOLD_TOKENS,
        target_tokens: int = TARGET_TOKENS_AFTER_COMPACTION,
        preserve_recent: int = PRESERVE_RECENT_TURNS,
        auto_trigger_ceiling: int = AUTO_COMPACTION_CEILING_80PCT,
        summarizer: Optional[SemanticSummarizer] = None
    ):
        self.threshold_tokens = threshold_tokens
        self.target_tokens = target_tokens
        self.preserve_recent = preserve_recent
        self.auto_trigger_ceiling = auto_trigger_ceiling
        self.summarizer = summarizer or SemanticSummarizer()
        self.differential_compactor = DifferentialStateCompactor(
            keep_recent=preserve_recent,
            keep_head=2  # Keep goal anchor + first user turn
        )
        self._compaction_history: List[CompactionResult] = []
    
    def estimate_history_tokens(self, history: List[Dict[str, Any]]) -> int:
        """Estimate total tokens in conversation history."""
        total = 0
        for msg in history:
            content = msg.get("content", "")
            if isinstance(content, str):
                total += estimate_tokens(content)
            elif isinstance(content, list):
                # Handle structured content (e.g., tool calls)
                for item in content:
                    if isinstance(item, dict):
                        total += estimate_tokens(str(item))
        return total
    
    def should_compact(self, history: List[Dict[str, Any]]) -> bool:
        """Check if compaction should trigger (token threshold or 80% ceiling)."""
        tot = self.estimate_history_tokens(history)
        return tot >= self.threshold_tokens or tot >= self.auto_trigger_ceiling
    
    def compact(self, history: List[Dict[str, Any]]) -> CompactionResult:
        """
        Compact history while preserving critical state.
        
        Preservation Priority (highest to lowest):
        1. GoalAnchor (messages[0] - immutable)
        2. ActivePlanState (.hermes/plan.json content)
        3. Active diffs/patches
        4. Most recent N turns
        5. Milestone verdicts (VERIFIED/FAILED)
        """
        original_tokens = self.estimate_history_tokens(history)
        
        if not self.should_compact(history):
            return CompactionResult(
                triggered=False,
                original_token_count=original_tokens,
                compacted_token_count=original_tokens,
                turns_compacted=0,
                turns_preserved=len(history),
                compaction_ratio=1.0
            )
        
        # Load active plan state for verbatim preservation
        plan_state = ActivePlanState.load()
        plan_block = plan_state.format_verbatim_block()
        plan_tokens = estimate_tokens(plan_block) if plan_block else 0
        
        # First, apply differential compaction (preserves milestones, recent turns)
        diff_compacted = self.differential_compactor.compact(history)
        
        # Then apply semantic summarization to remaining middle turns
        # Structure: [head(2)] + [middle] + [tail(preserve_recent)]
        keep_head = 2
        keep_tail = self.preserve_recent
        
        if len(diff_compacted) <= keep_head + keep_tail:
            # Already compact enough
            compacted_tokens = self.estimate_history_tokens(diff_compacted)
            return CompactionResult(
                triggered=True,
                original_token_count=original_tokens,
                compacted_token_count=compacted_tokens,
                turns_compacted=len(history) - len(diff_compacted),
                turns_preserved=len(diff_compacted),
                compaction_ratio=original_tokens / max(1, compacted_tokens)
            )
        
        head = diff_compacted[:keep_head]
        tail = diff_compacted[-keep_tail:]
        middle = diff_compacted[keep_head:-keep_tail]
        
        # Ingest full middle turn content into MoBA block router before summarization
        try:
            try:
                from .moba_context_router import get_moba_context_router
            except ImportError:
                from moba_context_router import get_moba_context_router
            moba = get_moba_context_router()
            archive_lines = [f"[{m.get('role', 'unknown')}]: {m.get('content', '')}" for m in middle]
            if archive_lines:
                moba.ingest_document("session_archive", "\n\n".join(archive_lines))
        except Exception:
            pass

        # Summarize middle turns
        summarized_middle = []
        summaries = []
        
        for i, msg in enumerate(middle):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            tool_calls = msg.get("tool_calls")
            tool_name = ""
            if tool_calls and len(tool_calls) > 0:
                tool_name = tool_calls[0].get("function", {}).get("name", "")
            
            original_content_tokens = estimate_tokens(str(content))
            
            # Check if this is a plan/diff turn that must be preserved verbatim
            is_plan_turn = self._is_plan_turn(msg, plan_state)
            is_diff_turn = self._is_diff_turn(msg)
            
            if is_plan_turn or is_diff_turn:
                # Preserve verbatim
                summarized_middle.append(msg)
                summaries.append(TurnSummary(
                    turn_index=i + keep_head,
                    role=role,
                    original_tokens=original_content_tokens,
                    summary=str(content),
                    summary_tokens=original_content_tokens,
                    preserved_verbatim=True
                ))
                continue
            
            # Generate semantic summary
            if role == "assistant":
                summary_text = self.summarizer.summarize_assistant_turn(str(content), tool_calls)
            elif role == "user":
                summary_text = self.summarizer.summarize_user_turn(str(content))
            elif role == "tool":
                summary_text = self.summarizer.summarize_tool_turn(str(content), tool_name)
            else:
                summary_text = self.summarizer._truncate_to_tokens(str(content))
            
            summary_tokens = estimate_tokens(summary_text)
            
            summarized_middle.append({
                "role": "user",  # Summaries injected as user context
                "content": f"[COMPACTED] {summary_text}"
            })
            
            summaries.append(TurnSummary(
                turn_index=i + keep_head,
                role=role,
                original_tokens=original_content_tokens,
                summary=summary_text,
                summary_tokens=summary_tokens,
                preserved_verbatim=False
            ))
        
        # Reassemble: head + plan_block (if not already in head) + summarized_middle + tail
        # Ensure plan state is in head
        final_history = list(head)
        
        # Add plan block if not already present in head
        if plan_block and not any(plan_block in str(m.get("content", "")) for m in head):
            final_history.append({"role": "user", "content": plan_block})
        
        final_history.extend(summarized_middle)
        
        # Track verbatim-preserved items in tail (recent turns with diffs/plans)
        for i, msg in enumerate(tail):
            role = msg.get("role", "unknown")
            content_str = msg.get("content", "")
            original_content_tokens = estimate_tokens(str(content_str))
            is_plan_turn = self._is_plan_turn(msg, plan_state)
            is_diff_turn = self._is_diff_turn(msg)
            if is_plan_turn or is_diff_turn:
                summaries.append(TurnSummary(
                    turn_index=len(diff_compacted) - keep_tail + i,
                    role=role,
                    original_tokens=original_content_tokens,
                    summary=str(content_str),
                    summary_tokens=original_content_tokens,
                    preserved_verbatim=True
                ))
        
        final_history.extend(tail)
        
        compacted_tokens = self.estimate_history_tokens(final_history)
        
        # If still over target, apply aggressive summarization to middle
        if compacted_tokens > self.target_tokens and len(summarized_middle) > 0:
            final_history = self._aggressive_compact(final_history, plan_block, keep_head, keep_tail)
            compacted_tokens = self.estimate_history_tokens(final_history)
        
        result = CompactionResult(
            triggered=True,
            original_token_count=original_tokens,
            compacted_token_count=compacted_tokens,
            turns_compacted=len(middle),
            turns_preserved=len(head) + len(tail) + sum(1 for s in summaries if s.preserved_verbatim),
            summaries=summaries,
            compaction_ratio=original_tokens / max(1, compacted_tokens)
        )
        
        self._compaction_history.append(result)
        return result
    
    def _is_plan_turn(self, msg: Dict[str, Any], plan_state: ActivePlanState) -> bool:
        """Check if message contains plan state that must be preserved."""
        content = str(msg.get("content", ""))
        return ("GOAL_ANCHOR" in content or "ACTIVE_PLAN_STATE" in content or 
                (plan_state.current_target and plan_state.current_target in content))
    
    def _is_diff_turn(self, msg: Dict[str, Any]) -> bool:
        """Check if message contains active diff/patch state."""
        content = str(msg.get("content", ""))
        return ("DIFF:" in content or "patch_file" in content or 
                "replacement_block" in content or "target_block" in content)
    
    def _aggressive_compact(
        self, 
        history: List[Dict], 
        plan_block: str, 
        keep_head: int, 
        keep_tail: int
    ) -> List[Dict]:
        """Aggressive compaction when still over target."""
        head = history[:keep_head]
        tail = history[-keep_tail:]
        middle = history[keep_head:-keep_tail]
        
        # Merge all middle into single summary
        if middle:
            combined = " | ".join([
                f"[{m.get('role')}]: {str(m.get('content', ''))[:100]}" 
                for m in middle
            ])
            merged_summary = self.summarizer._truncate_to_tokens(
                f"[COMPACTED SESSION] {combined}", 
                self.summarizer.max_summary_tokens * 3
            )
            middle = [{"role": "user", "content": merged_summary}]
        
        return head + middle + tail
    
    def get_compaction_stats(self) -> Dict[str, Any]:
        """Get statistics about compaction operations."""
        if not self._compaction_history:
            return {"total_compactions": 0}
        
        total = len(self._compaction_history)
        avg_ratio = sum(c.compaction_ratio for c in self._compaction_history) / total
        total_saved = sum(c.original_token_count - c.compacted_token_count for c in self._compaction_history)
        
        return {
            "total_compactions": total,
            "average_compaction_ratio": round(avg_ratio, 2),
            "total_tokens_saved": total_saved,
            "last_compaction": self._compaction_history[-1].timestamp
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def compact_history(history: List[Dict[str, Any]]) -> CompactionResult:
    """Convenience function for one-shot compaction."""
    gate = ContextCompactorGate()
    return gate.compact(history)


def should_compact(history: List[Dict[str, Any]]) -> bool:
    """Convenience function to check compaction trigger."""
    gate = ContextCompactorGate()
    return gate.should_compact(history)


def estimate_tokens_simple(history: List[Dict[str, Any]]) -> int:
    """Convenience function to estimate history tokens."""
    gate = ContextCompactorGate()
    return gate.estimate_history_tokens(history)


if __name__ == "__main__":
    # Self-test
    print("ContextCompactorGate self-test")
    
    # Create test history with ~5000 tokens
    test_history = [
        {"role": "user", "content": "Create a 3D solar system simulation with Three.js"},
        {"role": "assistant", "content": "I'll build this step by step. First, let me set up the project structure.", "tool_calls": []},
        {"role": "assistant", "content": "Creating the main HTML file with Three.js boilerplate...", "tool_calls": [
            {"function": {"name": "patch_file", "arguments": {"target_block": "", "replacement_block": "<html>...</html>"}}}
        ]},
        {"role": "tool", "content": "Successfully wrote index.html"},
        {"role": "assistant", "content": "Now adding the orbital mechanics calculations...", "tool_calls": []},
        {"role": "assistant", "content": "Implementing Kepler's laws for realistic orbits...", "tool_calls": []},
        {"role": "tool", "content": "PASS: Observer gate verified syntax and types"},
        {"role": "assistant", "content": "Adding planet textures and lighting...", "tool_calls": []},
        {"role": "tool", "content": "VERIFIED: All tests pass"},
    ] * 50  # Repeat to exceed threshold
    
    gate = ContextCompactorGate()
    print(f"Original tokens: {gate.estimate_history_tokens(test_history)}")
    print(f"Should compact: {gate.should_compact(test_history)}")
    
    result = gate.compact(test_history)
    print(f"Compacted tokens: {result.compacted_token_count}")
    print(f"Compaction ratio: {result.compaction_ratio:.2f}")
    print(f"Turns compacted: {result.turns_compacted}")
    print(f"Turns preserved: {result.turns_preserved}")
