#!/usr/bin/env python3.13
"""
Semantic Documentation & Capability Indexer (Roadmap 6 - Milestone 8b)
====================================================================
Crawls markdown documentation, architecture standards, and skill descriptions
to build a structured offline index for sub-millisecond retrieval.

Usage:
    python3.13 bin/index_docs.py [--query "<search_phrase>"]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def find_workspace_root() -> Path:
    p = Path(__file__).resolve()
    for parent in [p] + list(p.parents):
        if (parent / 'AGENTS.md').exists() or (parent / 'pyproject.toml').exists():
            return parent
    return Path.home() / "Projects/Workspace/Personal/hermes"


def build_doc_index(root: Path) -> list[dict]:
    docs = []
    # Key root documents
    key_files = ["AGENTS.md", "README.md", "Plan.md", "roadmap6.md"]
    for kf in key_files:
        p = root / kf
        if p.exists():
            content = p.read_text(encoding="utf-8", errors="replace")
            docs.append({
                "title": kf,
                "type": "standard_doc",
                "path": str(p),
                "sections": [s.strip() for s in content.split("\n## ") if s.strip()],
                "summary": content[:300].replace("\n", " ")
            })

    # Internal SOUL.md and skills
    hermes_dir = root / ".hermes" if (root / ".hermes").exists() else root / "private_dot_hermes"
    soul = hermes_dir / "SOUL.md"
    if soul.exists():
        content = soul.read_text(encoding="utf-8", errors="replace")
        docs.append({
            "title": "SOUL.md",
            "type": "cognitive_architecture",
            "path": str(soul),
            "sections": [s.strip() for s in content.split("\n## ") if s.strip()],
            "summary": content[:300].replace("\n", " ")
        })

    skills_dir = hermes_dir / "skills" if (hermes_dir / "skills").exists() else hermes_dir / "private_skills"
    if skills_dir.exists():
        for sf in skills_dir.rglob("SKILL.md"):
            content = sf.read_text(encoding="utf-8", errors="replace")
            docs.append({
                "title": f"skill:{sf.parent.name}",
                "type": "skill_manifest",
                "path": str(sf),
                "sections": [s.strip() for s in content.split("\n## ") if s.strip()],
                "summary": content[:200].replace("\n", " ")
            })

    return docs


def main():
    parser = argparse.ArgumentParser(description="Hermes Semantic Documentation Indexer")
    parser.add_argument("--query", type=str, default=None, help="Optional search query across docs")
    parser.add_argument("--json", action="store_true", help="Output full JSON index")
    args = parser.parse_args()

    root = find_workspace_root()
    index = build_doc_index(root)

    if args.query:
        words = set(args.query.lower().split())
        scored = []
        for doc in index:
            text = (doc["title"] + " " + doc["summary"] + " " + " ".join(doc["sections"][:3])).lower()
            doc_words = set(text.split())
            score = len(words & doc_words) / max(len(words), 1)
            if score > 0:
                scored.append((doc, score))
        scored.sort(key=lambda x: x[1], reverse=True)

        print(f"[+] Found {len(scored)} documents matching query: '{args.query}'\n")
        for doc, score in scored[:5]:
            print(f"  [{doc['type'].upper()}] {doc['title']} (Score: {score:.2f})")
            print(f"    Path:    {doc['path']}")
            print(f"    Summary: {doc['summary'][:120]}...\n")
    elif args.json:
        print(json.dumps(index, indent=2))
    else:
        print(f"[+] Successfully indexed {len(index)} documents and skill specifications across {root}")
        print(f"    - Core Architecture Docs: {sum(1 for d in index if d['type'] == 'standard_doc')}")
        print(f"    - Cognitive Spec:        {sum(1 for d in index if d['type'] == 'cognitive_architecture')}")
        print(f"    - Skill Specifications:  {sum(1 for d in index if d['type'] == 'skill_manifest')}")


if __name__ == "__main__":
    main()
