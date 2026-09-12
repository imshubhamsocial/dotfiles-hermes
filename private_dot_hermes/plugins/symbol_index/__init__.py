"""
Hermes Plugin: symbol_index & C4 Architecture Generator
======================================================
Structural AST Symbol Graph and Automated C4 Documentation Engine (Litho / deepwiki-rs pattern).
Analyzes source code ASTs, maps module dependencies, and generates professional C4 architecture
documentation with interactive Mermaid diagrams.
"""

from __future__ import annotations

import ast
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


class CodebaseSymbolIndex:
    """Parses codebase AST and builds structural module and symbol graphs."""

    SKIP_DIRS = {
        ".git", ".cache", ".hermes_archived", ".local_archived",
        "venv", ".venv", "node_modules", "__pycache__", "build", "dist"
    }

    def __init__(self, root_dir: Optional[Path] = None):
        self.root_dir = root_dir or Path.cwd()
        self.symbols: Dict[str, Dict[str, Any]] = {}
        self.module_graph: Dict[str, List[str]] = {}

    def scan(self) -> Dict[str, Any]:
        """Scans all Python files and extracts class, function, and import symbols."""
        self.symbols.clear()
        self.module_graph.clear()

        total_files = 0
        total_classes = 0
        total_functions = 0

        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS and not d.startswith(".")]
            for f in files:
                if f.endswith(".py"):
                    full_path = Path(root) / f
                    rel_path = str(full_path.relative_to(self.root_dir))
                    try:
                        source = full_path.read_text(encoding="utf-8", errors="replace")
                        tree = ast.parse(source)
                    except Exception:
                        continue

                    total_files += 1
                    mod_classes = []
                    mod_functions = []
                    mod_imports = []

                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            bases = [b.id for b in node.bases if isinstance(b, ast.Name)]
                            mod_classes.append({"name": node.name, "bases": bases, "line": node.lineno})
                            total_classes += 1
                        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            mod_functions.append({"name": node.name, "line": node.lineno})
                            total_functions += 1
                        elif isinstance(node, ast.Import):
                            for alias in node.names:
                                mod_imports.append(alias.name)
                        elif isinstance(node, ast.ImportFrom) and node.module:
                            mod_imports.append(node.module)

                    self.symbols[rel_path] = {
                        "classes": mod_classes,
                        "functions": mod_functions,
                        "imports": sorted(list(set(mod_imports))),
                    }
                    self.module_graph[rel_path] = sorted(list(set(mod_imports)))

        return {
            "total_files": total_files,
            "total_classes": total_classes,
            "total_functions": total_functions,
            "indexed_modules": len(self.symbols),
        }


class C4ArchitectureGenerator:
    """Generates professional C4 architecture diagrams and specifications (Litho pattern)."""

    @classmethod
    def generate(
        cls,
        index: CodebaseSymbolIndex,
        output_file: Optional[Path] = None,
    ) -> Dict[str, Any]:
        hermes_home = os.environ.get("HERMES_HOME")
        base = Path(hermes_home) if hermes_home else Path.home() / ".hermes"
        out_path = output_file or (base / "docs" / "architecture" / "overview.md")
        out_path.parent.mkdir(parents=True, exist_ok=True)

        stats = index.scan()

        md = f"""# Hermes Agent OS — C4 Architecture Specification

> **Generated**: {datetime.now(timezone.utc).isoformat()}  
> **Source Engine**: Litho AST Structural Analyzer (`symbol_index`)  
> **Codebase Scope**: {stats['total_files']} Python modules | {stats['total_classes']} Classes | {stats['total_functions']} Functions  

---

## Level 1: System Context Diagram

```mermaid
graph TD
    User["fa:fa-user Developer / Engineer"] -->|"Commands & Raw Prompts"| Hermes["fa:fa-terminal Hermes Agent OS (Unified Entry Point)"]
    Hermes -->|"Inference & Speculative MTP"| Llama["fa:fa-server Local llama-server (127.0.0.1:8138)"]
    Hermes -->|"Container Isolation"| Dbox["fa:fa-cube Fedora Distrobox (ws-hermes)"]
    Hermes -->|"Local File Mutations"| HostFS["fa:fa-folder-open Local Workspace Filesystem"]
    Hermes -->|"Hardware Guard"| GPU["fa:fa-microchip NVIDIA RTX 3050 Laptop (<=4,800 MiB)"]
```

---

## Level 2: Container Diagram (Hermes Agent OS Core)

```mermaid
graph TD
    CLI["Hermes CLI Subcommands"] --> Router["Hybrid Context Router (32K HOT / 256K WARM / COLD)"]
    CLI --> Shield["ECC AgentShield (Shannon Entropy + AST Blast + Hash Audit)"]
    CLI --> BPE["BPE Memory Workspace (belief.md + experience.db)"]
    CLI --> Reward["EvoHarness-RL Scorer (8 Golden Laws + FrogNano Frontier)"]
    CLI --> Skills["Frontier Skill Intelligence (Superpowers + XML Schema)"]
    CLI --> Index["AST Symbol Graph & C4 Generator (Litho Pattern)"]

    Shield --> EvidenceDB[("verification_evidence.db (SHA256 Audit Chain)")]
    BPE --> ExpDB[("experience.db (BPE Insights Ledger)")]
    Reward --> TrajectoryBuffer[("training_buffer (sft_data.jsonl)")]
    Router --> DiskCold[("Cold Context Disk Archive")]
```

---

## Level 3: Core Subsystems & Invariants

### 1. AgentShield Security Boundary
- **Shannon Entropy Scanner**: Detects credentials and tokens with $H > 4.6$.
- **Role Security Enforcer**: Strict Maker-Verifier isolation (`@architect` read-only, `@coder` mutations, `@tester` test-execution).
- **Cryptographic Audit Trail**: Merkle-style SHA256 chain recording every mutation.

### 2. Hybrid Context & Harness Engineering
- **Context Preservation**: Retains System-2 reasoning traces across turns.
- **Session Checkpoints**: Automatic state serialization for long-horizon task recovery.
- **Output-Token Budget Guard**: Prevents context exhaustion by preemptively compacting to warm tier.

### 3. Model Evolution & Self-Improvement
- **FrogNano Learnability Frontier**: Trains small local models via online task synthesis calibrated to $[0.3, 0.7]$ reward envelope.
- **NoRA Offline SFT**: Offline 4-bit QLoRA fine-tuning under strict $<= 4,500$ MiB VRAM envelope.

---

## Level 4: Codebase Module Inventory
"""
        for mod, details in sorted(index.symbols.items())[:25]:
            cls_names = [c["name"] for c in details["classes"]]
            fn_names = [fn["name"] for fn in details["functions"][:5]]
            md += "- **`" + mod + "`**\n"
            if cls_names:
                md += "  - Classes: `" + ", ".join(cls_names) + "`\n"
            if fn_names:
                md += "  - Functions: `" + ", ".join(fn_names) + "`...\n"

        out_path.write_text(md, encoding="utf-8")

        return {
            "output_path": str(out_path),
            "stats": stats,
            "status": "GENERATED_SUCCESSFULLY",
        }


_GLOBAL_SYMBOL_INDEX: Optional[CodebaseSymbolIndex] = None


def get_symbol_index() -> CodebaseSymbolIndex:
    global _GLOBAL_SYMBOL_INDEX
    if _GLOBAL_SYMBOL_INDEX is None:
        _GLOBAL_SYMBOL_INDEX = CodebaseSymbolIndex()
    return _GLOBAL_SYMBOL_INDEX


def register(ctx=None):
    """Registers symbol_index and C4 documentation generator into Hermes runtime."""
    if not ctx:
        return True

    idx = get_symbol_index()

    # Dynamic import of UnderstandAnythingEngine
    def _get_ua():
        core_p = Path(__file__).resolve().parents[2] / "hermes-agent" / "agent" / "core"
        if str(core_p) not in sys.path:
            sys.path.insert(0, str(core_p))
        from agent.core.understand_anything import get_ua_engine
        return get_ua_engine()

    if hasattr(ctx, "register_cli_command"):
        # 1. C4 Architecture Docs: hermes docs
        def setup_docs(parser):
            parser.description = "Generate and inspect C4 architecture documentation (Litho pattern)"
            sub = parser.add_subparsers(dest="docs_cmd")
            gen_p = sub.add_parser("generate", help="Generate full C4 architecture documentation and diagrams")
            gen_p.add_argument("--output", help="Custom output markdown file path")
            sub.add_parser("status", help="Show codebase symbol index statistics")

        def handle_docs(args):
            cmd = getattr(args, "docs_cmd", "generate") or "generate"
            if cmd == "generate":
                out = Path(args.output) if getattr(args, "output", None) else None
                res = C4ArchitectureGenerator.generate(idx, output_file=out)
                print(f"✓ C4 Architecture Documentation Generated (Litho Pattern):")
                print(f"  Target File:     {res['output_path']}")
                print(f"  Modules Scanned: {res['stats']['indexed_modules']}")
                print(f"  Classes Found:   {res['stats']['total_classes']}")
                print(f"  Functions Found: {res['stats']['total_functions']}")
                return 0
            elif cmd == "status":
                st = idx.scan()
                print(f"AST Symbol Index Status:")
                print(f"  Total Files:     {st['total_files']}")
                print(f"  Classes:         {st['total_classes']}")
                print(f"  Functions:       {st['total_functions']}")
                return 0
            return 0

        ctx.register_cli_command("docs", "Generate and view C4 architecture documentation", setup_docs, handle_docs)

        # 2. Understand Anything: hermes understand
        def setup_understand(parser):
            parser.description = "Build Understand-Anything codebase knowledge graph (.ua/knowledge-graph.json)"
            parser.add_argument("--output", "-o", help="Custom path for .ua/knowledge-graph.json")

        def handle_understand(args):
            ua = _get_ua()
            print("==> Analyzing workspace AST, architectural layers, and business domains...")
            st = ua.scan_workspace(incremental=True)
            out_p = Path(args.output) if getattr(args, "output", None) else None
            saved = ua.export_ua_json(out_p)
            print("✓ Understand-Anything Knowledge Graph generated:")
            print(f"  Graph Artifact:  {saved}")
            print(f"  Total Nodes:     {st['total_nodes']}")
            print(f"  Total Edges:     {st['total_edges']}")
            print(f"  Domains:         {st['domains_count']}")
            print(f"  Files Scanned:   {st['files_scanned']}")
            return 0

        ctx.register_cli_command("understand", "Build Understand-Anything knowledge graph (.ua/knowledge-graph.json)", setup_understand, handle_understand)

        # 3. Diff Impact Analysis: hermes impact <target>
        def setup_impact(parser):
            parser.description = "Perform diff impact & blast-radius ripple analysis before code changes"
            parser.add_argument("target", help="File path or symbol name to analyze")

        def handle_impact(args):
            ua = _get_ua()
            ua.scan_workspace(incremental=True)
            rep = ua.diff_impact_analysis([args.target])
            print(rep.render_markdown())
            return 0

        ctx.register_cli_command("impact", "Calculate blast radius and ripple impact of code changes", setup_impact, handle_impact)

    # 4. Native Slash Commands
    if hasattr(ctx, "register_command"):
        def slash_understand(raw_args: str) -> str:
            ua = _get_ua()
            st = ua.scan_workspace(incremental=True)
            out = ua.export_ua_json()
            return (
                f"**Understand-Anything**: Knowledge graph generated at `{out}`\\n"
                f"- Nodes: `{st['total_nodes']}` | Edges: `{st['total_edges']}` | Domains: `{st['domains_count']}`"
            )

        def slash_impact(raw_args: str) -> str:
            target = raw_args.strip()
            if not target:
                return "Usage: /impact <file_path_or_symbol>"
            ua = _get_ua()
            ua.scan_workspace(incremental=True)
            rep = ua.diff_impact_analysis([target])
            return rep.render_markdown()

        ctx.register_command("understand", "Generate Understand-Anything knowledge graph", slash_understand)
        ctx.register_command("impact", "Analyze blast radius of modified symbols or files", slash_impact)

    return True


__all__ = [
    "CodebaseSymbolIndex",
    "C4ArchitectureGenerator",
    "get_symbol_index",
    "register",
]
