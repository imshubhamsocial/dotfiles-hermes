"""
Humanizer Plugin & Output Filter (Milestone U66)
================================================
Eliminates robotic throat-clearing, apologetic conversational filler, and redundant
AI boilerplates, transforming responses into dense, factual, professional engineering prose.

Preserves:
  - Code blocks verbatim
  - Metric tables and JSON payloads
  - File/line citation links
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Tuple

ROBOTIC_PREFIX_PATTERNS = [
    r"^(?:Certainly!|Sure!|Of course!|I\'d be happy to help(?: with that)?!?)[\s,]*",
    r"^(?:As an AI language model|As an AI assistant),?[\s,]*",
    r"^(?:Here is the solution|Here is the code you requested|Here are the requested changes):?[\s,]*",
    r"^(?:I have analyzed your request and|Based on your instructions, I will)[\s,]*",
    r"^(?:Great question!|Thank you for reaching out!|I understand you want to)[\s,]*",
    r"^(?:Let me break this down for you:?)[\s,]*",
]

ROBOTIC_SUFFIX_PATTERNS = [
    r"(?:\n+)?(?:Let me know if you (?:have any other questions|need further assistance|need more help)[\.\!]?)$",
    r"(?:\n+)?(?:I hope this helps(?: with your project)?[\.\!]?)$",
    r"(?:\n+)?(?:Feel free to ask if you (?:have any doubts|need anything else)[\.\!]?)$",
    r"(?:\n+)?(?:Happy coding[\.\!]?)$",
]


@dataclass
class HumanizerResult:
    original_text: str
    humanized_text: str
    transformations_applied: List[str]
    tokens_saved: int


class Humanizer:
    """Deterministic filter removing conversational fluff from agent outputs."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    def humanize(self, text: str) -> HumanizerResult:
        if not self.enabled or not text.strip():
            return HumanizerResult(
                original_text=text,
                humanized_text=text,
                transformations_applied=[],
                tokens_saved=0,
            )

        transformations = []
        cleaned = text

        # Strip prefixes from the opening (if not inside code block)
        if not cleaned.lstrip().startswith("```"):
            for pattern in ROBOTIC_PREFIX_PATTERNS:
                match = re.search(pattern, cleaned, flags=re.IGNORECASE | re.MULTILINE)
                if match and match.start() == 0:
                    cleaned = cleaned[match.end():].lstrip()
                    transformations.append(f"Stripped prefix pattern: {pattern[:25]}...")

        # Strip suffixes from the ending (if not inside code block)
        if not cleaned.rstrip().endswith("```"):
            for pattern in ROBOTIC_SUFFIX_PATTERNS:
                match = re.search(pattern, cleaned, flags=re.IGNORECASE)
                if match and match.end() == len(cleaned):
                    cleaned = cleaned[:match.start()].rstrip()
                    transformations.append(f"Stripped suffix pattern: {pattern[:25]}...")

        # Replace repeated empty lines (> 2 newlines -> 2 newlines)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

        orig_toks = len(text.split())
        new_toks = len(cleaned.split())
        saved = max(0, orig_toks - new_toks)

        return HumanizerResult(
            original_text=text,
            humanized_text=cleaned,
            transformations_applied=transformations,
            tokens_saved=saved,
        )


def create_humanizer(enabled: bool = True) -> Humanizer:
    return Humanizer(enabled=enabled)
