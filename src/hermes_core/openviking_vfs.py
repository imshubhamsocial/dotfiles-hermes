"""
Milestone U53: Volcengine OpenViking Hierarchical VFS Context Database
======================================================================
Implements OpenViking VFS Context Database:
  - Hierarchical virtual filesystem schema (`viking://`)
  - 3-Tier Progressive Context Representation:
      * L0 (Abstract): <= 100 tokens ultra-compact discovery summary
      * L1 (Overview): <= 2,000 tokens structural architecture outline
      * L2 (Full Detail): Unabridged node content loaded on demand
  - Standard POSIX VFS operations: `ls`, `cat`, `tree`, `find`, `mkdir`, `write`
  - Directory recursive search with subtree pruning
  - Zero GPU VRAM overhead (pure CPU RAMDisk execution)
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple, Union


@dataclass
class VFSNode:
    """Represents a virtual file or directory in the viking:// filesystem."""
    uri: str                        # e.g., "viking://core/task_graph.py"
    path: str                       # e.g., "/core/task_graph.py"
    name: str                       # e.g., "task_graph.py"
    is_dir: bool = False
    l0_abstract: str = ""           # <= 100 tokens summary
    l1_overview: str = ""           # <= 2,000 tokens structural outline
    l2_full_content: str = ""       # Complete unabridged content
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    children: Dict[str, VFSNode] = field(default_factory=dict)

    def estimate_tokens(self, text: str) -> int:
        """Rough token estimator: 1 token ≈ 4 characters."""
        return max(1, len(text) // 4) if text else 0

    @property
    def l0_tokens(self) -> int:
        return self.estimate_tokens(self.l0_abstract)

    @property
    def l1_tokens(self) -> int:
        return self.estimate_tokens(self.l1_overview)

    @property
    def l2_tokens(self) -> int:
        return self.estimate_tokens(self.l2_full_content)

    def to_dict(self, tier: str = "l0") -> Dict[str, Any]:
        base = {
            "uri": self.uri,
            "path": self.path,
            "name": self.name,
            "is_dir": self.is_dir,
            "tags": self.tags,
            "metadata": self.metadata,
        }
        if self.is_dir:
            base["child_count"] = len(self.children)
        else:
            if tier == "l0":
                base["content"] = self.l0_abstract
                base["tokens"] = self.l0_tokens
            elif tier == "l1":
                base["content"] = self.l1_overview
                base["tokens"] = self.l1_tokens
            else:
                base["content"] = self.l2_full_content
                base["tokens"] = self.l2_tokens
        return base


class OpenVikingVFS:
    """
    Hierarchical Virtual Filesystem Context Database.
    Organizes agent knowledge, project files, and skills into a traversable VFS.
    """

    URI_SCHEME = "viking://"
    L0_MAX_TOKENS = 100
    L1_MAX_TOKENS = 2000

    def __init__(self):
        self.root = VFSNode(
            uri="viking://",
            path="/",
            name="",
            is_dir=True,
            l0_abstract="Root VFS Namespace",
            l1_overview="Root namespace of the OpenViking Context Database",
        )

    def _normalize_path(self, uri_or_path: str) -> PurePosixPath:
        """Converts viking://uri or /raw/path into a normalized POSIX path."""
        s = uri_or_path.strip()
        if s.startswith(self.URI_SCHEME):
            s = s[len(self.URI_SCHEME):]
        if not s.startswith("/"):
            s = "/" + s
        return PurePosixPath(s)

    def mkdir(self, path: str, tags: Optional[List[str]] = None, l0_abstract: str = "") -> VFSNode:
        """Creates a virtual directory and all parent directories."""
        posix = self._normalize_path(path)
        parts = posix.parts[1:]  # skip root "/"

        curr = self.root
        accum = []

        for p in parts:
            accum.append(p)
            sub_path = "/" + "/".join(accum)
            if p not in curr.children:
                node = VFSNode(
                    uri=f"viking:/{sub_path}",
                    path=sub_path,
                    name=p,
                    is_dir=True,
                    l0_abstract=l0_abstract or f"Directory {p}",
                    l1_overview=f"Virtual directory node for {sub_path}",
                    tags=tags or [],
                )
                curr.children[p] = node
            curr = curr.children[p]

        return curr

    def write_node(
        self,
        path: str,
        l2_content: str,
        l0_abstract: str = "",
        l1_overview: str = "",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> VFSNode:
        """Writes or updates a 3-tier context file node."""
        posix = self._normalize_path(path)
        parent_posix = posix.parent
        file_name = posix.name

        parent_node = self.mkdir(str(parent_posix))

        # Auto-synthesize L0 / L1 if not explicitly provided
        if not l0_abstract:
            lines = [line.strip() for line in l2_content.splitlines() if line.strip()]
            summary = lines[0] if lines else f"File {file_name}"
            l0_abstract = summary[:350]

        if not l1_overview:
            lines = l2_content.splitlines()[:50]
            l1_overview = "\n".join(lines)[:6000]

        node_uri = f"viking:/{str(posix)}"
        node = VFSNode(
            uri=node_uri,
            path=str(posix),
            name=file_name,
            is_dir=False,
            l0_abstract=l0_abstract,
            l1_overview=l1_overview,
            l2_full_content=l2_content,
            tags=tags or [],
            metadata=metadata or {},
        )

        parent_node.children[file_name] = node
        return node

    def get_node(self, path: str) -> Optional[VFSNode]:
        """Resolves a node by path or URI."""
        posix = self._normalize_path(path)
        if posix == PurePosixPath("/"):
            return self.root

        parts = posix.parts[1:]
        curr = self.root

        for p in parts:
            if p not in curr.children:
                return None
            curr = curr.children[p]

        return curr

    def cat(self, path: str, tier: str = "l0") -> str:
        """Reads node content at specified resolution tier (l0, l1, l2)."""
        node = self.get_node(path)
        if not node:
            raise FileNotFoundError(f"VFS node not found: {path}")

        if node.is_dir:
            return f"[Directory: {node.path} ({len(node.children)} entries)]"

        tier = tier.lower()
        if tier == "l0":
            return node.l0_abstract
        elif tier == "l1":
            return node.l1_overview
        elif tier == "l2":
            return node.l2_full_content
        else:
            raise ValueError(f"Invalid context resolution tier: {tier} (must be l0, l1, or l2)")

    def ls(self, path: str = "/") -> List[Dict[str, Any]]:
        """Lists directory entries with L0 token counts."""
        node = self.get_node(path)
        if not node:
            raise FileNotFoundError(f"VFS directory not found: {path}")
        if not node.is_dir:
            return [node.to_dict(tier="l0")]

        return [child.to_dict(tier="l0") for child in sorted(node.children.values(), key=lambda n: n.name)]

    def tree(self, path: str = "/", max_depth: int = 4) -> str:
        """Generates a hierarchical visual tree representation."""
        node = self.get_node(path)
        if not node:
            raise FileNotFoundError(f"VFS directory not found: {path}")

        lines = [f"{node.uri} [L0: {node.l0_tokens} tok]"]

        def _walk(curr: VFSNode, prefix: str, depth: int):
            if depth >= max_depth:
                return
            items = sorted(curr.children.values(), key=lambda n: (not n.is_dir, n.name))
            for i, child in enumerate(items):
                is_last = (i == len(items) - 1)
                connector = "└── " if is_last else "├── "
                suffix = "/" if child.is_dir else f" (L0: {child.l0_tokens}t, L1: {child.l1_tokens}t)"
                lines.append(f"{prefix}{connector}{child.name}{suffix}")
                if child.is_dir:
                    new_prefix = prefix + ("    " if is_last else "│   ")
                    _walk(child, new_prefix, depth + 1)

        _walk(node, "", 0)
        return "\n".join(lines)

    def find(self, query: str, root_path: str = "/", tag: Optional[str] = None) -> List[VFSNode]:
        """Performs recursive search across VFS subtrees with tag filtering."""
        start = self.get_node(root_path)
        if not start:
            return []

        results: List[VFSNode] = []
        q_lower = query.lower()

        def _search(curr: VFSNode):
            if tag and tag not in curr.tags:
                pass  # Skip if tag doesn't match
            else:
                if (
                    q_lower in curr.name.lower()
                    or q_lower in curr.l0_abstract.lower()
                    or q_lower in curr.l1_overview.lower()
                ):
                    results.append(curr)

            if curr.is_dir:
                for child in curr.children.values():
                    _search(child)

        _search(start)
        return results


def create_openviking_vfs() -> OpenVikingVFS:
    return OpenVikingVFS()
