"""
Hierarchical Context Anchoring & Progressive Rule Walker for Google AGY.
Follows the Antigravity 2.0 "Closer is Better" rule priority:
- Layer 0: Global user settings (~/.gemini/antigravity-cli/settings.json, ~/.agents/)
- Layer 1: Project root manifest (AGENTS.md / GEMINI.md)
- Layer 2: Scoped subdirectories (src/.../.agents/rules.md)
Enforces Progressive Disclosure (L0 -> L1 -> L2) to cap prompt injection under 400 tokens.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class ProgressiveRule:
    """Represents a rule with progressive disclosure levels."""

    def __init__(
        self,
        source_path: Path,
        layer: int,
        title: str,
        frontmatter: Dict[str, str],
        summary: str,
        full_content: str,
    ):
        self.source_path = source_path
        self.layer = layer
        self.title = title
        self.frontmatter = frontmatter
        self.summary = summary
        self.full_content = full_content

    def get_disclosure_text(self, level: int = 1) -> str:
        """Returns rule text at level 0 (trigger), 1 (summary), or 2 (full content)."""
        if level == 0:
            desc = self.frontmatter.get("description", self.summary[:100])
            return f"- **{self.title}** (Layer {self.layer}): {desc}"
        elif level == 1:
            return f"### {self.title} [Layer {self.layer}]\n{self.summary}"
        else:
            return f"### {self.title} [Layer {self.layer} - Full]\n{self.full_content}"


class HierarchicalRuleWalker:
    """Discovers, merges, and progressively renders hierarchical project rules."""

    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = workspace_root or Path.cwd()
        self.rules: List[ProgressiveRule] = []
        self.refresh()

    def refresh(self):
        """Scans filesystem hierarchy and compiles active rules."""
        self.rules = []
        # Layer 0: Global defaults
        self._scan_global_rules()
        # Layer 1: Project root AGENTS.md / GEMINI.md
        self._scan_root_manifest()
        # Layer 2: Scoped subdirectories
        self._scan_scoped_rules()

    def _parse_rule_file(self, file_path: Path, layer: int) -> Optional[ProgressiveRule]:
        if not file_path.exists() or not file_path.is_file():
            return None
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        if not content.strip():
            return None

        # Extract YAML frontmatter if present
        frontmatter = {}
        fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
        if fm_match:
            raw_fm, body = fm_match.group(1), fm_match.group(2)
            for line in raw_fm.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    frontmatter[k.strip()] = v.strip().strip("\"'")
        else:
            body = content

        title = frontmatter.get("name") or file_path.stem.upper()
        # Extract summary (first non-empty paragraph or 200 chars)
        paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
        summary = paragraphs[0] if paragraphs else body[:200]

        return ProgressiveRule(
            source_path=file_path,
            layer=layer,
            title=title,
            frontmatter=frontmatter,
            summary=summary,
            full_content=body,
        )

    def _scan_global_rules(self):
        """Layer 0: scans ~/.agents/ or ~/.gemini/."""
        home = Path.home()
        global_candidates = [
            home / ".agents" / "AGENTS.md",
            home / ".agents" / "rules.md",
            home / ".gemini" / "antigravity-cli" / "AGENTS.md",
        ]
        for path in global_candidates:
            rule = self._parse_rule_file(path, layer=0)
            if rule:
                self.rules.append(rule)

    def _scan_root_manifest(self):
        """Layer 1: scans workspace root for AGENTS.md / GEMINI.md."""
        candidates = [
            self.workspace_root / "AGENTS.md",
            self.workspace_root / "GEMINI.md",
            self.workspace_root / ".agents.md",
        ]
        found = False
        for path in candidates:
            rule = self._parse_rule_file(path, layer=1)
            if rule:
                self.rules.append(rule)
                found = True
                break

    def _scan_scoped_rules(self):
        """Layer 2: scans subdirectories for .agents/rules.md."""
        try:
            for path in self.workspace_root.glob("*/.agents/rules.md"):
                rule = self._parse_rule_file(path, layer=2)
                if rule:
                    self.rules.append(rule)
        except Exception:
            pass

    def compile_prompt_context(self, target_path: Optional[str] = None, max_tokens: int = 400) -> str:
        """Assembles progressive disclosure context within strict token budgets."""
        # Closer is better: Layer 2 > Layer 1 > Layer 0
        sorted_rules = sorted(self.rules, key=lambda r: r.layer, reverse=True)
        if not sorted_rules:
            return ""

        sections = ["## Progressive Rules Hierarchy (Antigravity 2.0)"]
        estimated_chars = 0
        max_chars = max_tokens * 4

        for rule in sorted_rules:
            # If target_path provided, check if scoped rule applies
            if target_path and rule.layer == 2:
                # Only include if target_path is within rule directory
                rule_dir = str(rule.source_path.parent.parent)
                if not str(Path(target_path).resolve()).startswith(str(Path(rule_dir).resolve())):
                    continue

            rule_text = rule.get_disclosure_text(level=1)
            if estimated_chars + len(rule_text) <= max_chars:
                sections.append(rule_text)
                estimated_chars += len(rule_text)
            else:
                # Degrade to Level 0
                l0_text = rule.get_disclosure_text(level=0)
                if estimated_chars + len(l0_text) <= max_chars:
                    sections.append(l0_text)
                    estimated_chars += len(l0_text)

        return "\n\n".join(sections)
