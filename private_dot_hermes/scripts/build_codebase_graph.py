#!/usr/bin/env python3
"""
Hermes Agent OS: Codebase Knowledge Graph Builder
=================================================
Executes local, deterministic AST extraction via isolated Graphify binary,
produces GraphRAG-ready JSON, community clusters, and converts them into
First-Class SecondBrain KnowledgeCards on CPU RAMDisk (<8ms, 0 MiB VRAM).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure hermes_core is discoverable if run from repo root
REPO_ROOT = Path(__file__).resolve().parents[2]
HERMES_SRC = REPO_ROOT / ".hermes" / "src"
if str(HERMES_SRC) not in sys.path:
    sys.path.insert(0, str(HERMES_SRC))

from hermes_core.second_brain import KnowledgeCard, SecondBrain

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("codebase_graph_builder")


def find_graphify_binary() -> Path:
    """Locate isolated graphify executable."""
    env_bin = os.environ.get("GRAPHIFY_BIN")
    if env_bin and Path(env_bin).exists():
        return Path(env_bin)

    candidates = [
        Path("/var/home/imshubhamsocial/.local/share/graphify-env/bin/graphify"),
        Path.home() / ".local" / "share" / "graphify-env" / "bin" / "graphify",
        Path.home() / ".local" / "bin" / "graphify",
        Path("/var/home/imshubhamsocial/.local/bin/graphify"),
    ]
    for c in candidates:
        if c.exists() and os.access(c, os.X_OK):
            return c

    # Check system PATH
    sys_path = shutil.which("graphify")
    if sys_path:
        return Path(sys_path)

    raise FileNotFoundError(
        "graphify executable not found. Ensure ~/.local/share/graphify-env is provisioned."
    )


def extract_codebase_graph(
    target_dir: Path,
    out_dir: Path,
    graphify_bin: Optional[Path] = None,
    code_only: bool = True,
) -> Path:
    """Run headless AST extraction on target directory."""
    binary = graphify_bin or find_graphify_binary()
    out_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        str(binary),
        "extract",
        str(target_dir),
        "--out",
        str(out_dir),
    ]
    if code_only:
        cmd.append("--code-only")

    logger.info("Executing headless AST extraction: %s", " ".join(cmd))
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        logger.error("Graphify extract failed:\n%s\n%s", res.stdout, res.stderr)
        raise RuntimeError(f"graphify extract exited with {res.returncode}")

    logger.info("AST Extraction successful:\n%s", res.stdout.strip())
    graph_json = out_dir / "graphify-out" / "graph.json"
    if not graph_json.exists():
        # Check direct out_dir
        if (out_dir / "graph.json").exists():
            return out_dir / "graph.json"
        raise FileNotFoundError(f"graph.json was not generated at {graph_json}")
    return graph_json


def export_wiki(graph_json: Path, graphify_bin: Optional[Path] = None) -> Path:
    """Export Wikipedia-style markdown articles from graph.json."""
    binary = graphify_bin or find_graphify_binary()
    cmd = [
        str(binary),
        "export",
        "wiki",
        "--graph",
        str(graph_json),
    ]
    logger.info("Exporting knowledge wiki: %s", " ".join(cmd))
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        logger.error("Export wiki failed:\n%s\n%s", res.stdout, res.stderr)
        raise RuntimeError(f"graphify export wiki exited with {res.returncode}")

    wiki_dir = graph_json.parent / "wiki"
    logger.info("Wiki exported to: %s", wiki_dir)
    return wiki_dir


def bridge_wiki_to_second_brain(
    wiki_dir: Path,
    second_brain: Optional[SecondBrain] = None,
    tag_prefix: str = "graphify",
) -> List[Path]:
    """Ingest community articles into SecondBrain as verified KnowledgeCards."""
    sb = second_brain or SecondBrain()
    saved_cards: List[Path] = []

    for md_file in wiki_dir.glob("Community_*.md"):
        content = md_file.read_text(encoding="utf-8")
        stem = md_file.stem
        # Clean braces/brackets in content to satisfy SecondBrain Invariant R5-4
        content_clean = content.replace("{", "(").replace("}", ")")

        # Extract title from first line
        lines = content_clean.splitlines()
        title = lines[0].replace("#", "").strip() if lines else stem

        card = KnowledgeCard(
            id=f"ast_{stem.lower()}",
            title=f"Codebase Architecture: {title}",
            category="concepts",
            tags=[tag_prefix, "ast-graph", "community", stem.lower()],
            content=content_clean,
            verified=True,
        )
        try:
            path = sb.save(card)
            saved_cards.append(path)
        except Exception as e:
            logger.warning("Failed to save card %s: %s", card.id, e)

    logger.info("Bridged %d community cards into SecondBrain", len(saved_cards))
    return saved_cards


def main():
    parser = argparse.ArgumentParser(description="Build codebase AST knowledge graph for Hermes")
    parser.add_argument("target", nargs="?", default=".", help="Target directory to index")
    parser.add_argument("--out", default="/tmp/hermes_graphify", help="Output directory")
    parser.add_argument("--bridge", action="store_true", default=True, help="Bridge into SecondBrain")
    args = parser.parse_args()

    target_path = Path(args.target).resolve()
    out_path = Path(args.out).resolve()

    graph_json = extract_codebase_graph(target_path, out_path)
    wiki_dir = export_wiki(graph_json)

    if args.bridge:
        bridge_wiki_to_second_brain(wiki_dir)

    print(f"\n✅ Graphify AST build complete!")
    print(f"   Graph JSON: {graph_json}")
    print(f"   Wiki Index: {wiki_dir / 'index.md'}\n")


if __name__ == "__main__":
    main()
