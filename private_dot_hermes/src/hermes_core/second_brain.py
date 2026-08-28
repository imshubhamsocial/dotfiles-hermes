"""
Cross-Session Second Brain Knowledge Vault (Milestone U64 & Invariant R5-4)
==========================================================================
Persistent, structured Markdown knowledge repository with frontmatter metadata:
  ~/.hermes/knowledge/
    ├── concepts/     # Domain models and high-level architectural patterns
    ├── blueprints/   # Verified canonical blueprints, templates & specs
    ├── evals/        # Benchmark results, evaluation runs & leaderboard records
    ├── profiles/     # User profile, environment variables & hardware configs
    ├── evidence/     # Research citations, deep crawl results & evidence logs
    └── skills/       # Dynamic learned skills from reflective sessions (L3 Tier)

Enforces Invariant R5-4: Second-Brain-Commit-Gate.
"""

from __future__ import annotations

import datetime
import os
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


CATEGORIES = {"concepts", "blueprints", "evals", "profiles", "evidence", "skills"}


@dataclass
class KnowledgeCard:
    id: str
    title: str
    category: str
    content: str
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    verified: bool = True
    filepath: Optional[str] = None

    def to_markdown(self) -> str:
        tag_str = ", ".join(self.tags)
        return (
            f"---\n"
            f"id: \"{self.id}\"\n"
            f"title: \"{self.title}\"\n"
            f"category: \"{self.category}\"\n"
            f"tags: [{tag_str}]\n"
            f"created_at: \"{self.created_at}\"\n"
            f"updated_at: \"{self.updated_at}\"\n"
            f"verified: {str(self.verified).lower()}\n"
            f"---\n\n"
            f"# {self.title}\n\n"
            f"{self.content.strip()}\n"
        )


class SecondBrain:
    """Manager for the persistent cross-session knowledge vault."""

    def __init__(self, root_dir: Optional[Path] = None):
        self.root_dir = root_dir or (Path.home() / ".hermes" / "knowledge")
        self._ensure_structure()

    def _ensure_structure(self) -> None:
        self.root_dir.mkdir(parents=True, exist_ok=True)
        for cat in CATEGORIES:
            (self.root_dir / cat).mkdir(exist_ok=True)

    def validate_card(self, card: KnowledgeCard) -> Tuple[bool, List[str]]:
        """Invariant R5-4 Gate: Verify card integrity before commitment."""
        errors = []
        if not card.id or not re.match(r"^[a-zA-Z0-9_\-]+$", card.id):
            errors.append(f"Invalid card ID '{card.id}'. Must be alphanumeric with hyphens/underscores.")
        if card.category not in CATEGORIES:
            errors.append(f"Invalid category '{card.category}'. Must be one of {CATEGORIES}")
        if not card.title.strip():
            errors.append("Title cannot be empty.")
        if not card.content.strip():
            errors.append("Content cannot be empty.")
        # Brace parity check
        if card.content.count("{") != card.content.count("}"):
            errors.append("Unbalanced curly braces in card content.")
        if card.content.count("[") != card.content.count("]"):
            errors.append("Unbalanced square brackets in card content.")
        return len(errors) == 0, errors

    def save(self, card: KnowledgeCard) -> Path:
        valid, errors = self.validate_card(card)
        if not valid:
            raise ValueError(f"Second Brain Commit Gate Rejected Card: {'; '.join(errors)}")

        cat_dir = self.root_dir / card.category
        cat_dir.mkdir(parents=True, exist_ok=True)
        target_file = cat_dir / f"{card.id}.md"

        card.updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        md_text = card.to_markdown()
        target_file.write_text(md_text, encoding="utf-8")
        card.filepath = str(target_file)
        return target_file

    def get(self, category: str, card_id: str) -> Optional[KnowledgeCard]:
        target_file = self.root_dir / category / f"{card_id}.md"
        if not target_file.exists():
            return None
        return self._parse_file(target_file)

    def search(self, query: str, category: Optional[str] = None, max_results: int = 5) -> List[KnowledgeCard]:
        q_tokens = [w.lower() for w in re.findall(r"\b[a-zA-Z0-9_\-]+\b", query)]
        results: List[Tuple[KnowledgeCard, int]] = []

        categories = [category] if category and category in CATEGORIES else list(CATEGORIES)
        for cat in categories:
            cat_dir = self.root_dir / cat
            if not cat_dir.exists():
                continue
            for md_path in cat_dir.glob("*.md"):
                card = self._parse_file(md_path)
                if not card:
                    continue
                text = f"{card.title} {card.content} {' '.join(card.tags)}".lower()
                hits = sum(text.count(qt) for qt in q_tokens)
                if hits > 0:
                    results.append((card, hits))

        results.sort(key=lambda x: x[1], reverse=True)
        return [r[0] for r in results[:max_results]]

    def list_cards(self, category: Optional[str] = None) -> List[KnowledgeCard]:
        categories = [category] if category and category in CATEGORIES else list(CATEGORIES)
        cards = []
        for cat in categories:
            cat_dir = self.root_dir / cat
            if not cat_dir.exists():
                continue
            for md_path in cat_dir.glob("*.md"):
                c = self._parse_file(md_path)
                if c:
                    cards.append(c)
        return cards

    def _parse_file(self, path: Path) -> Optional[KnowledgeCard]:
        try:
            content = path.read_text(encoding="utf-8")
            if not content.startswith("---"):
                return None
            parts = content.split("---", 2)
            if len(parts) < 3:
                return None

            fm_raw = parts[1]
            body = parts[2].strip()
            if body.startswith("# "):
                body = body.split("\n", 1)[1].strip() if "\n" in body else ""

            card_id = path.stem
            title = card_id
            category = path.parent.name
            tags = []
            created_at = ""
            updated_at = ""
            verified = True

            for line in fm_raw.splitlines():
                if line.startswith("id:"):
                    card_id = line.split("id:", 1)[1].strip().strip('"\'')
                elif line.startswith("title:"):
                    title = line.split("title:", 1)[1].strip().strip('"\'')
                elif line.startswith("category:"):
                    category = line.split("category:", 1)[1].strip().strip('"\'')
                elif line.startswith("tags:"):
                    raw_tags = line.split("tags:", 1)[1].strip().strip("[]")
                    tags = [t.strip().strip('"\'') for t in raw_tags.split(",") if t.strip()]
                elif line.startswith("created_at:"):
                    created_at = line.split("created_at:", 1)[1].strip().strip('"\'')
                elif line.startswith("updated_at:"):
                    updated_at = line.split("updated_at:", 1)[1].strip().strip('"\'')
                elif line.startswith("verified:"):
                    verified = line.split("verified:", 1)[1].strip().lower() == "true"

            return KnowledgeCard(
                id=card_id,
                title=title,
                category=category,
                content=body,
                tags=tags,
                created_at=created_at or datetime.datetime.now(datetime.timezone.utc).isoformat(),
                updated_at=updated_at or datetime.datetime.now(datetime.timezone.utc).isoformat(),
                verified=verified,
                filepath=str(path),
            )
        except Exception:
            return None


def create_second_brain(root_dir: Optional[Path] = None) -> SecondBrain:
    return SecondBrain(root_dir=root_dir)
