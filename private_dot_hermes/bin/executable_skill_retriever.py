#!/usr/bin/env python3.13
"""
State-Grounded Dynamic Skill Retrieval Engine (Roadmap 6 - Milestone 2)
======================================================================
Retrieves modular procedural skills from the Hermes Skill Library based on
current task state vectors using FastEmbed (BGE CPU ONNX). Preserves prefix-cache
determinism by injecting minimal canonical skills strictly at the prompt tail.

Usage:
    python3.13 bin/skill_retriever.py "<task_state_query>" [--top-k 3] [--json]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


def find_skills_root() -> Path:
    candidates = [
        Path.home() / ".hermes/skills",
        Path.home() / ".hermes/private_skills",
        Path(__file__).resolve().parents[1] / "private_skills",
        Path(__file__).resolve().parents[1] / "skills",
    ]
    for c in candidates:
        if c.exists() and c.is_dir():
            return c
    return Path.home() / ".hermes/skills"


class SkillRetriever:
    def __init__(self, skills_dir: Path | None = None, top_k: int = 3):
        self.skills_dir = skills_dir or find_skills_root()
        self.top_k = top_k
        self.catalog = self._load_catalog()

    def _load_catalog(self) -> List[Dict[str, Any]]:
        catalog = []
        if not self.skills_dir.exists():
            return catalog

        for skill_file in self.skills_dir.rglob("SKILL.md"):
            try:
                content = skill_file.read_text(encoding="utf-8")
                lines = content.splitlines()
                desc = ""
                name = skill_file.parent.name
                # Parse frontmatter description
                in_fm = False
                for line in lines:
                    if line.strip() == "---":
                        in_fm = not in_fm
                        continue
                    if in_fm and line.startswith("description:"):
                        desc = line.split(":", 1)[1].strip().strip('"').strip("'")
                        break
                if not desc and len(lines) > 2:
                    desc = lines[1].strip()[:100]

                catalog.append({
                    "name": name,
                    "category": skill_file.parent.parent.name,
                    "path": str(skill_file),
                    "description": desc,
                    "content": content[:1500]  # Store concise snippet
                })
            except Exception:
                continue
        return catalog

    def query(self, task_state: str) -> List[Tuple[Dict[str, Any], float]]:
        if not self.catalog:
            return []

        # Try dense neural retrieval with fastembed on CPU
        try:
            from fastembed import TextEmbedding
            # Use small, CPU-optimized model
            model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
            
            docs = [f"{s['name']}: {s['description']}" for s in self.catalog]
            doc_embeddings = list(model.embed(docs))
            query_embedding = list(model.embed([task_state]))[0]

            import numpy as np
            q_vec = np.array(query_embedding)
            scores = []
            for idx, d_vec in enumerate(doc_embeddings):
                d_arr = np.array(d_vec)
                sim = float(np.dot(q_vec, d_arr) / (np.linalg.norm(q_vec) * np.linalg.norm(d_arr) + 1e-9))
                scores.append((self.catalog[idx], sim))

            scores.sort(key=lambda x: x[1], reverse=True)
            return scores[:self.top_k]
        except Exception:
            # Fallback to token-matching BM25 / jaccard similarity
            words = set(task_state.lower().split())
            scores = []
            for item in self.catalog:
                target_words = set((item["name"] + " " + item["description"]).lower().split())
                overlap = len(words & target_words)
                score = overlap / max(len(words | target_words), 1)
                scores.append((item, score))
            scores.sort(key=lambda x: x[1], reverse=True)
            return scores[:self.top_k]


def main():
    parser = argparse.ArgumentParser(description="State-Grounded Skill Retrieval Engine")
    parser.add_argument("query", type=str, help="Current task state or engineering goal")
    parser.add_argument("--top-k", type=int, default=3, help="Number of skills to retrieve")
    parser.add_argument("--json", action="store_true", help="Output JSON result")
    args = parser.parse_args()

    retriever = SkillRetriever(top_k=args.top_k)
    results = retriever.query(args.query)

    if args.json:
        out = [
            {
                "name": item["name"],
                "category": item["category"],
                "score": round(score, 4),
                "description": item["description"],
                "path": item["path"]
            }
            for item, score in results
        ]
        print(json.dumps(out, indent=2))
    else:
        print(f"Top {len(results)} skills retrieved for task: '{args.query}'\n")
        for rank, (item, score) in enumerate(results, 1):
            print(f"{rank}. [{item['category']}/{item['name']}] (Relevance: {score:.3f})")
            print(f"   Description: {item['description']}")
            print(f"   Path: {item['path']}\n")


if __name__ == "__main__":
    main()
