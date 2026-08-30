"""
4-Tier Skill Hierarchy Engine & BM25 Router (Milestone U63 & Invariant R5-2)
===========================================================================
Implements a 4-tier progressive context injector for skills:
  - Tier L3 (Learnt): Learned skills from reflective feedback (Highest Priority)
  - Tier L2 (User/Repo): Project-specific repository skills in .hermes/skills/
  - Tier L1 (Agent): User home agent skills & Antigravity skills (~/.hermes/skills/)
  - Tier L0 (Main): Canonical upstream Hermes agent skills (.hermes/hermes-agent/skills/)

Enforces Invariant R5-2: Single-Skill-Per-Turn (<= 200 tokens injected).
"""

from __future__ import annotations

import math
import os
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class SkillStub:
    name: str
    tier: str  # "L3_LEARNT", "L2_REPO", "L1_AGENT", "L0_MAIN"
    description: str
    path: str
    triggers: List[str] = field(default_factory=list)
    content: str = ""
    token_count: int = 0


@dataclass
class RoutedSkill:
    matched: bool
    skill: Optional[SkillStub] = None
    score: float = 0.0
    injected_prompt: str = ""
    token_count: int = 0


class BM25SkillIndex:
    """Lightweight in-memory BM25 index over SkillStubs."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus: List[SkillStub] = []
        self.doc_tokens: List[List[str]] = []
        self.doc_lens: List[int] = []
        self.avgdl: float = 0.0
        self.df: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}

    def _tokenize(self, text: str) -> List[str]:
        return [w.lower() for w in re.findall(r"\b[a-zA-Z0-9_\-]+\b", text)]

    def index(self, skills: List[SkillStub]) -> None:
        self.corpus = skills
        self.doc_tokens = []
        self.doc_lens = []
        self.df = {}

        for skill in self.corpus:
            tokens = self._tokenize(f"{skill.name} {skill.description} {' '.join(skill.triggers)}")
            self.doc_tokens.append(tokens)
            self.doc_lens.append(len(tokens))
            unique_terms = set(tokens)
            for t in unique_terms:
                self.df[t] = self.df.get(t, 0) + 1

        n_docs = len(self.corpus)
        if n_docs > 0:
            self.avgdl = sum(self.doc_lens) / n_docs
            for t, count in self.df.items():
                self.idf[t] = math.log((n_docs - count + 0.5) / (count + 0.5) + 1.0)
        else:
            self.avgdl = 0.0

    def search(self, query: str) -> List[Tuple[SkillStub, float]]:
        q_tokens = self._tokenize(query)
        if not q_tokens or not self.corpus:
            return []

        scores: List[Tuple[SkillStub, float]] = []
        # Priority multiplier for hierarchy: L3 (1.5x) > L2 (1.3x) > L1 (1.1x) > L0 (1.0x)
        tier_multipliers = {
            "L3_LEARNT": 1.5,
            "L2_REPO": 1.3,
            "L1_AGENT": 1.1,
            "L0_MAIN": 1.0,
        }

        for idx, (doc, d_len) in enumerate(zip(self.doc_tokens, self.doc_lens)):
            score = 0.0
            doc_counts = {}
            for t in doc:
                doc_counts[t] = doc_counts.get(t, 0) + 1

            for qt in q_tokens:
                if qt in doc_counts:
                    tf = doc_counts[qt]
                    idf = self.idf.get(qt, 0.0)
                    denom = tf + self.k1 * (1.0 - self.b + self.b * (d_len / (self.avgdl or 1.0)))
                    score += idf * ((tf * (self.k1 + 1.0)) / denom)

            # Apply tier multiplier
            mult = tier_multipliers.get(self.corpus[idx].tier, 1.0)
            final_score = score * mult
            if final_score > 0.1:
                scores.append((self.corpus[idx], final_score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores


class FourTierSkillRouter:
    """4-tier skill discovery and single-skill progressive context injector."""

    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = repo_root or Path(os.getcwd())
        self.home_dir = Path.home()
        self.index = BM25SkillIndex()
        self.skills: List[SkillStub] = []
        self.reload_catalog()

    def reload_catalog(self) -> None:
        self.skills = []
        # Tier L3: Learnt Skills
        l3_path = self.home_dir / ".hermes" / "knowledge" / "skills"
        self._scan_skill_directory(l3_path, "L3_LEARNT")

        # Tier L2: User/Repo Skills
        l2_path = self.repo_root / ".hermes" / "skills"
        self._scan_skill_directory(l2_path, "L2_REPO")

        # Tier L1: Agent Skills
        l1_path = self.home_dir / ".hermes" / "skills"
        if l1_path != l2_path:
            self._scan_skill_directory(l1_path, "L1_AGENT")

        # Tier L0: Main Hermes Skills
        l0_path = self.repo_root / ".hermes" / "hermes-agent" / "skills"
        if not l0_path.exists():
            l0_path = self.home_dir / ".hermes" / "hermes-agent" / "skills"
        self._scan_skill_directory(l0_path, "L0_MAIN")

        self.index.index(self.skills)

    def _scan_skill_directory(self, base_dir: Path, tier: str) -> None:
        if not base_dir.exists():
            return
        for skill_md in base_dir.rglob("SKILL.md"):
            try:
                stub = self._parse_skill_file(skill_md, tier)
                if stub:
                    self.skills.append(stub)
            except Exception:
                continue

    def _parse_skill_file(self, path: Path, tier: str) -> Optional[SkillStub]:
        content = path.read_text(encoding="utf-8")
        name = path.parent.name
        description = ""
        triggers = []

        # Parse YAML frontmatter if present
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                fm = parts[1]
                for line in fm.splitlines():
                    if line.startswith("name:"):
                        name = line.split("name:", 1)[1].strip().strip('"\'')
                    elif line.startswith("description:"):
                        description = line.split("description:", 1)[1].strip().strip('"\'')
                    elif line.startswith("triggers:"):
                        raw_trig = line.split("triggers:", 1)[1].strip()
                        triggers = [t.strip(" []\"'") for t in raw_trig.split(",")]

        if not description:
            # Fallback to first non-empty lines
            lines = [l.strip() for l in content.splitlines() if l.strip() and not l.startswith("#")]
            description = lines[0] if lines else f"Skill {name}"

        return SkillStub(
            name=name,
            tier=tier,
            description=description,
            path=str(path),
            triggers=triggers,
            content=content,
            token_count=len(content.split()),
        )

    def route(self, prompt: str, max_tokens: int = 200) -> RoutedSkill:
        """Route prompt and return exactly 1 high-relevance skill clamped to max_tokens."""
        matches = self.index.search(prompt)
        if not matches:
            return RoutedSkill(matched=False, token_count=0)

        best_skill, score = matches[0]
        # Format compact injection
        injected = self._format_compact_injection(best_skill, max_tokens)
        tok_count = len(injected.split())

        return RoutedSkill(
            matched=True,
            skill=best_skill,
            score=score,
            injected_prompt=injected,
            token_count=tok_count,
        )

    def _format_compact_injection(self, skill: SkillStub, max_tokens: int) -> str:
        header = f"### [SKILL ACTIVE: {skill.name} ({skill.tier})]\n"
        body = skill.description
        # Extract main rules/instructions if available
        lines = [l for l in skill.content.splitlines() if not l.startswith("---")]
        text_content = "\n".join(lines[:12]).strip()
        combined = f"{header}{text_content}"

        words = combined.split()
        if len(words) > max_tokens:
            combined = " ".join(words[:max_tokens]) + "\n..."
        return combined


def create_skill_router(repo_root: Optional[Path] = None) -> FourTierSkillRouter:
    return FourTierSkillRouter(repo_root=repo_root)
