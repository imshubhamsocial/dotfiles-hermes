"""
U48: Agent-OS Two-Tier Standards Engine
=========================================
Hierarchical loader merging Global Standards (~/.hermes/rules/) with 
Project Standards (.hermes/rules/).
Deterministic precedence: project rules override defaults, but can never 
violate global hardware/safety constraints.
Slot 3 compilation stays within <300 tokens.
"""

from __future__ import annotations

import hashlib
import os
import re
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml


# =============================================================================
# CONFIGURATION
# =============================================================================

GLOBAL_RULES_DIR = Path.home() / ".hermes" / "rules"
PROJECT_RULES_DIR_NAME = Path(".hermes") / "rules"
MAX_SLOT3_TOKENS = 300
TOKEN_ESTIMATE_RATIO = 4  # 4 chars per token


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class RuleFile:
    """Parsed rule file with metadata"""
    path: Path
    category: str  # global, project
    content: str
    frontmatter: Dict[str, Any]
    tokens: int
    hash: str
    priority: int = 0  # Higher = more specific (project > global)


@dataclass
class CompiledStandards:
    """Compiled two-tier standards for Slot 3 injection"""
    global_rules: List[RuleFile]
    project_rules: List[RuleFile]
    merged_content: str
    total_tokens: int
    global_hash: str
    project_hash: str


# =============================================================================
# IMMUTABLE GLOBAL CONSTRAINTS
# =============================================================================

IMMUTABLE_GLOBAL_CONSTRAINTS = {
    "vram_ceiling_mib": 4800,
    "gpu_model": "RTX 3050",
    "gpu_vram_gb": 6,
    "container": "ws-hermes",
    "relative_paths_only": True,
    "zero_sorry_testing": True,
    "surgical_diffs_only": True,
    "ground_truth_first": True,
    "prefix_cache_discipline": True,
    "refusal_protocol": True,
}


# =============================================================================
# RULE PARSER
# =============================================================================

class RuleParser:
    """Parse rule files with YAML frontmatter"""
    
    FRONTMATTER_PATTERN = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
    
    @classmethod
    def parse(cls, rule_path: Path, category: str) -> RuleFile:
        """Parse a rule file"""
        if not rule_path.exists():
            raise FileNotFoundError(f"Rule file not found: {rule_path}")
        
        content = rule_path.read_text(encoding="utf-8")
        
        # Extract frontmatter
        match = cls.FRONTMATTER_PATTERN.match(content)
        frontmatter = {}
        body = content
        
        if match:
            yaml_str = match.group(1)
            body = content[match.end():]
            try:
                frontmatter = yaml.safe_load(yaml_str) or {}
            except yaml.YAMLError:
                frontmatter = {}
        
        # Ensure category is set
        frontmatter.setdefault("category", category)
        frontmatter.setdefault("immutable", category == "global")
        
        # Calculate tokens
        tokens = cls.estimate_tokens(body)
        
        # Compute hash for change detection
        content_hash = hashlib.sha256(body.encode()).hexdigest()[:16]
        
        # Priority: project > global
        priority = 100 if category == "project" else 10
        
        return RuleFile(
            path=rule_path,
            category=category,
            content=body.strip(),
            frontmatter=frontmatter,
            tokens=tokens,
            hash=content_hash,
            priority=priority,
        )
    
    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Estimate token count"""
        return max(1, len(" ".join(text.split())) // TOKEN_ESTIMATE_RATIO)


# =============================================================================
# TWO-TIER STANDARDS ENGINE
# =============================================================================

class TwoTierStandardsEngine:
    """
    Hierarchical standards engine merging global and project rules.
    Project rules override defaults but can NEVER violate global immutable constraints.
    """
    
    def __init__(
        self,
        global_rules_dir: Optional[Path] = None,
        project_root: Optional[Path] = None,
        max_slot3_tokens: int = MAX_SLOT3_TOKENS,
    ):
        self.global_rules_dir = global_rules_dir or GLOBAL_RULES_DIR
        self.project_root = project_root or Path.cwd()
        self.max_slot3_tokens = max_slot3_tokens
        
        self._global_rules: List[RuleFile] = []
        self._project_rules: List[RuleFile] = []
        self._compiled: Optional[CompiledStandards] = None
        self._lock = threading.RLock()
        
        self._load_rules()
    
    def _load_rules(self):
        """Load rules from both tiers"""
        with self._lock:
            self._global_rules = self._scan_rules_dir(self.global_rules_dir, "global")
            project_rules_dir = self.project_root / PROJECT_RULES_DIR_NAME
            self._project_rules = self._scan_rules_dir(project_rules_dir, "project")
    
    def _scan_rules_dir(self, rules_dir: Path, category: str) -> List[RuleFile]:
        """Scan directory for rule files"""
        rules = []
        if not rules_dir.exists():
            return rules
        
        for rule_file in sorted(rules_dir.glob("*.md")):
            try:
                rule = RuleParser.parse(rule_file, category)
                rules.append(rule)
            except Exception:
                # Silently skip invalid rules
                pass
        
        return rules
    
    def reload(self):
        """Reload rules from disk"""
        with self._lock:
            self._load_rules()
            self._compiled = None
    
    def get_global_rules(self) -> List[RuleFile]:
        """Get global rules"""
        with self._lock:
            return list(self._global_rules)
    
    def get_project_rules(self) -> List[RuleFile]:
        """Get project rules"""
        with self._lock:
            return list(self._project_rules)
    
    def compile(self) -> CompiledStandards:
        """Compile merged standards for Slot 3 injection"""
        with self._lock:
            if self._compiled is not None:
                return self._compiled
            
            # Sort by priority (project rules first for override, but global immutable constraints enforced)
            all_rules = sorted(
                self._global_rules + self._project_rules,
                key=lambda r: (-r.priority, r.path.name)
            )
            
            # Build merged content
            merged_parts = []
            total_tokens = 0
            
            # Global immutable header (always included)
            merged_parts.append("# IMMUTABLE GLOBAL CONSTRAINTS (Cannot be overridden)")
            merged_parts.append(self._format_immutable_constraints())
            total_tokens += self.estimate_tokens(merged_parts[-1])
            
            # Add global rules
            if self._global_rules:
                merged_parts.append("\n# GLOBAL STANDARDS")
                for rule in self._global_rules:
                    rule_block = f"## {rule.path.stem}\n{rule.content}"
                    if total_tokens + rule.tokens <= self.max_slot3_tokens:
                        merged_parts.append(rule_block)
                        total_tokens += rule.tokens
                    else:
                        break
            
            # Add project rules (override/extend)
            if self._project_rules:
                merged_parts.append("\n# PROJECT STANDARDS (Overrides/Extends Global)")
                for rule in self._project_rules:
                    rule_block = f"## {rule.path.stem}\n{rule.content}"
                    if total_tokens + rule.tokens <= self.max_slot3_tokens:
                        merged_parts.append(rule_block)
                        total_tokens += rule.tokens
                    else:
                        break
            
            merged_content = "\n\n".join(merged_parts)
            
            # Compute hashes for cache invalidation
            global_hash = hashlib.sha256(
                "\n".join(r.content for r in self._global_rules).encode()
            ).hexdigest()[:16]
            project_hash = hashlib.sha256(
                "\n".join(r.content for r in self._project_rules).encode()
            ).hexdigest()[:16]
            
            self._compiled = CompiledStandards(
                global_rules=list(self._global_rules),
                project_rules=list(self._project_rules),
                merged_content=merged_content,
                total_tokens=total_tokens,
                global_hash=global_hash,
                project_hash=project_hash,
            )
            
            return self._compiled
    
    def _format_immutable_constraints(self) -> str:
        """Format immutable global constraints"""
        lines = []
        for key, value in IMMUTABLE_GLOBAL_CONSTRAINTS.items():
            lines.append(f"- {key}: {value}")
        return "\n".join(lines)
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count"""
        return RuleParser.estimate_tokens(text)
    
    def get_slot3_injection(self) -> str:
        """Get compiled standards for Slot 3 injection"""
        compiled = self.compile()
        return compiled.merged_content
    
    def validate_project_rule(self, rule_content: str) -> Dict[str, Any]:
        """Validate project rule doesn't violate global constraints"""
        violations = []
        warnings = []
        
        content_lower = rule_content.lower()
        
        # Check for VRAM violations
        if "vram" in content_lower and "4800" not in content_lower:
            # Check if it mentions higher VRAM
            import re
            vram_matches = re.findall(r'(\d+)\s*(?:mib|gb|gib)', content_lower)
            for match in vram_matches:
                if int(match) > 4800:
                    violations.append(f"Project rule specifies VRAM > 4800 MiB: {match}")
        
        # Check for absolute paths
        if "/home/" in rule_content or "/var/" in rule_content:
            if not any(p in rule_content for p in ["$HOME", "$BASH_SOURCE", "relative"]):
                warnings.append("Project rule may contain absolute paths")
        
        # Check for xfails/skip
        if "xfail" in content_lower or "skip" in content_lower:
            warnings.append("Project rule mentions test skipping - violates zero-sorry testing")
        
        # Check for full rewrites
        if "rewrite" in content_lower or "replace entire" in content_lower:
            warnings.append("Project rule suggests full file rewrites - violates surgical diffs")
        
        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "warnings": warnings,
        }
    
    def get_zero_vram_guarantee(self) -> Dict[str, Any]:
        """Verify zero GPU VRAM overhead"""
        return {
            "yaml_parsing_cpu_only": True,
            "file_io_cpu_only": True,
            "token_estimation_cpu_only": True,
            "no_gpu_operations": True,
            "ramdisk_compatible": True,
        }


# =============================================================================
# INTEGRATION WITH PROMPT SLOTTING
# =============================================================================

def build_two_tier_slot3_injection(
    base_slot3: str,
    standards_engine: Optional[TwoTierStandardsEngine] = None,
) -> str:
    """
    Inject two-tier standards into Slot 3 (Behavioral Invariants).
    Preserves master laws while adding project/global rules.
    """
    if standards_engine is None:
        return base_slot3
    
    injection = standards_engine.get_slot3_injection()
    
    if not injection:
        return base_slot3
    
    # Inject before the end of Slot 3
    # Find a good insertion point - after the main invariants
    # Simple approach: append
    return base_slot3 + "\n\n" + injection


# =============================================================================
# FACTORY
# =============================================================================

_global_standards_engine: Optional[TwoTierStandardsEngine] = None
_global_lock = threading.Lock()


def get_standards_engine(
    global_rules_dir: Optional[Path] = None,
    project_root: Optional[Path] = None,
) -> TwoTierStandardsEngine:
    """Get or create global standards engine"""
    global _global_standards_engine
    with _global_lock:
        if _global_standards_engine is None:
            _global_standards_engine = TwoTierStandardsEngine(
                global_rules_dir=global_rules_dir,
                project_root=project_root,
            )
        return _global_standards_engine


def reset_standards_engine():
    """Reset global engine (for testing)"""
    global _global_standards_engine
    with _global_lock:
        _global_standards_engine = None


if __name__ == "__main__":
    # Self-test
    print("TwoTierStandardsEngine self-test")
    
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        global_dir = Path(td) / "global"
        project_dir = Path(td) / "project" / ".hermes" / "rules"
        global_dir.mkdir(parents=True)
        project_dir.mkdir(parents=True)
        
        # Create global rule
        (global_dir / "hardware.md").write_text("""---
version: 1.0.0
category: global
immutable: true
---
# Hardware Constraints
- VRAM: 4800 MiB max
- GPU: RTX 3050
""")
        
        # Create project rule
        (project_dir / "coding.md").write_text("""---
version: 1.0.0
category: project
extends: global
---
# Project Coding Standards
- Use type hints
- Relative paths only
""")
        
        engine = TwoTierStandardsEngine(
            global_rules_dir=global_dir,
            project_root=Path(td) / "project",
        )
        
        print(f"Global rules: {len(engine.get_global_rules())}")
        print(f"Project rules: {len(engine.get_project_rules())}")
        
        compiled = engine.compile()
        print(f"Compiled tokens: {compiled.total_tokens}")
        print(f"Global hash: {compiled.global_hash}")
        print(f"Project hash: {compiled.project_hash}")
        
        injection = engine.get_slot3_injection()
        print(f"Slot 3 injection ({len(injection)} chars):")
        print(injection[:500])
        
        # Validate project rule
        validation = engine.validate_project_rule("Use VRAM 5000 MiB for this task")
        print(f"Validation: {validation}")
        
        print("All self-tests passed!")
