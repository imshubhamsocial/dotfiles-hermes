"""
GitHub Ingestion & Workplace Repo Maintenance (Milestone U28)
==============================================================
Automated codebase ingestion, stack detection, dependency bootstrap,
test framework auto-discovery, and AST symbol graph indexing.

Features:
  1. Tech Stack & Language Detection (Python, TypeScript/JavaScript, Rust, Go, C/C++)
  2. Dependency Manifest Discovery (pyproject.toml, requirements.txt, package.json, Cargo.toml)
  3. Test Runner Auto-Discovery (pytest, jest, vitest, cargo test, go test)
  4. Automatic AST Knowledge Graph Ingestion (SymbolGraph U22 integration)
  5. Workplace Baseline Report Synthesis
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any

from hermes_core.symbol_graph import SymbolGraph, create_memory_graph


@dataclass
class ProjectStackInfo:
    primary_language: str
    languages: List[str]
    manifests: List[str]
    test_framework: Optional[str]
    test_command: Optional[str]
    symbol_count: int
    files_indexed: int
    entrypoints: List[str] = field(default_factory=list)


class RepoOnboarder:
    """
    Onboards repositories into the Hermes Agent OS substrate.
    """

    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = Path(workspace_root) if workspace_root else Path.cwd()

    def detect_stack(self, target_dir: Optional[Path] = None) -> ProjectStackInfo:
        """
        Inspects directory tree and identifies language, package managers, and test runners.
        """
        root = Path(target_dir) if target_dir else self.workspace_root
        languages = set()
        manifests = []
        entrypoints = []
        test_framework = None
        test_command = None

        # 1. Manifest discovery
        manifest_checks = [
            ("pyproject.toml", "Python", "pytest", "pytest"),
            ("requirements.txt", "Python", "pytest", "pytest"),
            ("setup.py", "Python", "pytest", "pytest"),
            ("package.json", "JavaScript/TypeScript", "jest/vitest", "npm test"),
            ("Cargo.toml", "Rust", "cargo test", "cargo test"),
            ("go.mod", "Go", "go test", "go test ./..."),
            ("CMakeLists.txt", "C/C++", "ctest", "ctest"),
            ("Makefile", "Generic/Make", None, "make test"),
        ]

        for fname, lang, test_fw, test_cmd in manifest_checks:
            if (root / fname).exists():
                manifests.append(fname)
                languages.add(lang)
                if not test_framework and test_fw:
                    test_framework = test_fw
                    test_command = test_cmd

        # 2. File extension sampling
        ext_map = {
            ".py": "Python",
            ".ts": "TypeScript",
            ".js": "JavaScript",
            ".rs": "Rust",
            ".go": "Go",
            ".cpp": "C++",
            ".c": "C",
            ".html": "HTML/Web",
        }

        file_counts: Dict[str, int] = {}
        for p in root.rglob("*"):
            if p.is_file() and not any(part.startswith((".", "__", "node_modules", "target", "venv")) for part in p.parts):
                ext = p.suffix.lower()
                if ext in ext_map:
                    lang = ext_map[ext]
                    languages.add(lang)
                    file_counts[lang] = file_counts.get(lang, 0) + 1
                if p.name in ("main.py", "app.py", "index.ts", "index.js", "main.rs", "main.go"):
                    entrypoints.append(str(p.relative_to(root)))

        primary = max(file_counts, key=file_counts.get) if file_counts else (list(languages)[0] if languages else "Unknown")

        return ProjectStackInfo(
            primary_language=primary,
            languages=sorted(list(languages)),
            manifests=manifests,
            test_framework=test_framework,
            test_command=test_command,
            symbol_count=0,
            files_indexed=0,
            entrypoints=entrypoints[:5],
        )

    def onboard(self, target_dir: Optional[Path] = None, index_symbols: bool = True) -> ProjectStackInfo:
        """
        Runs full onboarding pipeline: stack detection + symbol indexing.
        """
        root = Path(target_dir) if target_dir else self.workspace_root
        stack_info = self.detect_stack(root)

        if index_symbols and "Python" in stack_info.languages:
            graph = create_memory_graph()
            stats = graph.index_directory(str(root))
            stack_info.files_indexed = stats.get("files_indexed", 0)
            stack_info.symbol_count = stats.get("total_symbols", stats.get("symbols_indexed", 0))
            graph.close()

        return stack_info

    def generate_onboarding_summary(self, stack_info: ProjectStackInfo) -> str:
        """
        Produces a concise Markdown summary for Agent OS context.
        """
        lines = [
            "# Repository Onboarding Report",
            f"- **Primary Stack**: `{stack_info.primary_language}`",
            f"- **Detected Languages**: {', '.join(stack_info.languages) if stack_info.languages else 'None'}",
            f"- **Manifests**: {', '.join(stack_info.manifests) if stack_info.manifests else 'None'}",
            f"- **Test Suite**: `{stack_info.test_command or 'Auto-detect required'}` ({stack_info.test_framework or 'None'})",
            f"- **Indexed Knowledge**: {stack_info.symbol_count} symbols across {stack_info.files_indexed} files",
        ]
        if stack_info.entrypoints:
            lines.append(f"- **Discovered Entrypoints**: {', '.join(stack_info.entrypoints)}")
        return "\n".join(lines)


def create_repo_onboarder(workspace_root: Optional[Path] = None) -> RepoOnboarder:
    """Factory helper creating RepoOnboarder instance."""
    return RepoOnboarder(workspace_root=workspace_root)


__all__ = [
    "ProjectStackInfo",
    "RepoOnboarder",
    "create_repo_onboarder",
]
