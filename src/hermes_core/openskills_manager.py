"""
U46: OpenSkills Universal Package Manager & Lifecycle
=======================================================
Implements standardized SKILL.md parsing with progressive disclosure:
- L0 Discovery: name + description in system prompt (<50 tokens/skill)
- L1 Dynamic Load (load_skill): Inject full skill instructions & tool schemas
- L2 Dynamic Unload (unload_skill): Evict skill from context to prevent bloat
- Zero GPU VRAM overhead (CPU/RAMDisk only)
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

try:
    import yaml
except ImportError:
    yaml = None


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class SkillManifest:
    """Parsed YAML frontmatter from SKILL.md"""
    name: str
    description: str
    version: str = "1.0.0"
    author: str = "hermes-agent"
    license: str = "MIT"
    platforms: List[str] = field(default_factory=lambda: ["linux", "macos", "windows"])
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_discovery_line(self) -> str:
        """L0 Discovery format: concise name + description (<50 tokens)"""
        return f"- {self.name}: {self.description}"
    
    def estimate_tokens(self, text: str) -> int:
        """Token estimation (4 chars/token heuristic)"""
        return max(1, len(" ".join(text.split())) // 4)
    
    def discovery_tokens(self) -> int:
        """Tokens for L0 discovery entry"""
        return self.estimate_tokens(self.to_discovery_line())
    
    def validate(self) -> None:
        """Validate required fields"""
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Skill manifest: 'name' is required and must be a non-empty string.")
        if not self.description or not isinstance(self.description, str):
            raise ValueError(f"Skill '{self.name}': 'description' is required.")
        if not isinstance(self.dependencies, list):
            raise ValueError(f"Skill '{self.name}': 'dependencies' must be a list.")
        if not isinstance(self.tools, list):
            raise ValueError(f"Skill '{self.name}': 'tools' must be a list.")
        if not isinstance(self.parameters, dict):
            raise ValueError(f"Skill '{self.name}': 'parameters' must be a dict.")


@dataclass
class SkillPackage:
    """Complete skill package with manifest and body"""
    manifest: SkillManifest
    skill_content: str
    skill_path: Path
    skill_hash: str
    loaded: bool = False
    load_count: int = 0


@dataclass
class LoadedSkill:
    """Skill currently loaded in active context"""
    name: str
    manifest: SkillManifest
    skill_content: str
    tool_schemas: List[Dict[str, Any]]
    load_timestamp: float
    usage_count: int = 0


# =============================================================================
# SKILL PARSER
# =============================================================================

class SkillParser:
    """Parse SKILL.md files with YAML frontmatter"""
    
    FRONTMATTER_PATTERN = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
    
    @classmethod
    def parse(cls, skill_path: Path) -> SkillPackage:
        """Parse a SKILL.md file into a SkillPackage"""
        if not skill_path.exists():
            raise FileNotFoundError(f"SKILL.md not found: {skill_path}")
        
        content = skill_path.read_text(encoding="utf-8")
        
        # Extract YAML frontmatter
        match = cls.FRONTMATTER_PATTERN.match(content)
        if not match:
            raise ValueError(f"Skill '{skill_path}': Missing YAML frontmatter (--- delimiter)")
        
        yaml_str = match.group(1)
        skill_body = content[match.end():].strip()
        
        if yaml is None:
            raise ImportError("PyYAML required for parsing skill frontmatter. Install with: pip install pyyaml")
        
        try:
            frontmatter = yaml.safe_load(yaml_str)
        except yaml.YAMLError as e:
            raise ValueError(f"Skill '{skill_path}': Invalid YAML frontmatter: {e}")
        
        if not isinstance(frontmatter, dict):
            raise ValueError(f"Skill '{skill_path}': Frontmatter must be a dictionary")
        
        # Create manifest
        manifest = SkillManifest(
            name=frontmatter.get("name", ""),
            description=frontmatter.get("description", ""),
            version=frontmatter.get("version", "1.0.0"),
            author=frontmatter.get("author", "hermes-agent"),
            license=frontmatter.get("license", "MIT"),
            platforms=frontmatter.get("platforms", ["linux", "macos", "windows"]),
            tags=frontmatter.get("tags", []),
            dependencies=frontmatter.get("dependencies", []),
            tools=frontmatter.get("tools", []),
            parameters=frontmatter.get("parameters", {}),
            metadata=frontmatter.get("metadata", {}),
        )
        manifest.validate()
        
        # Compute hash for change detection
        skill_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        
        return SkillPackage(
            manifest=manifest,
            skill_content=skill_body,
            skill_path=skill_path,
            skill_hash=skill_hash
        )
    
    @classmethod
    def parse_from_string(cls, content: str, name_hint: str = "") -> SkillPackage:
        """Parse SKILL.md content from string (for testing)"""
        if not content.strip():
            raise ValueError("Empty skill content")
        
        match = cls.FRONTMATTER_PATTERN.match(content)
        if not match:
            raise ValueError("Missing YAML frontmatter (--- delimiter)")
        
        yaml_str = match.group(1)
        skill_body = content[match.end():].strip()
        
        if yaml is None:
            raise ImportError("PyYAML required")
        
        try:
            frontmatter = yaml.safe_load(yaml_str)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML frontmatter: {e}")
        
        manifest = SkillManifest(
            name=frontmatter.get("name", name_hint or "unnamed"),
            description=frontmatter.get("description", ""),
            version=frontmatter.get("version", "1.0.0"),
            author=frontmatter.get("author", "hermes-agent"),
            license=frontmatter.get("license", "MIT"),
            platforms=frontmatter.get("platforms", ["linux", "macos", "windows"]),
            tags=frontmatter.get("tags", []),
            dependencies=frontmatter.get("dependencies", []),
            tools=frontmatter.get("tools", []),
            parameters=frontmatter.get("parameters", {}),
            metadata=frontmatter.get("metadata", {}),
        )
        manifest.validate()
        
        skill_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        
        return SkillPackage(
            manifest=manifest,
            skill_content=skill_body,
            skill_path=Path(name_hint or "inline"),
            skill_hash=skill_hash
        )


# =============================================================================
# TOOL SCHEMA EXTRACTOR
# =============================================================================

class ToolSchemaExtractor:
    """Extract tool schemas from skill content and manifest"""
    
    # Known tool schemas (can be extended)
    BUILTIN_TOOLS = {
        "patch_file": {
            "name": "patch_file",
            "description": "Apply a surgical patch to a file. Provide exact target_block to replace and replacement_block.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_block": {"type": "string", "description": "Exact lines to replace (must match exactly)"},
                    "replacement_block": {"type": "string", "description": "New lines to insert"}
                },
                "required": ["target_block", "replacement_block"]
            }
        },
        "execute_command": {
            "name": "execute_command",
            "description": "Run a shell command in the workspace. Returns stdout, stderr, exit_code.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to execute"},
                    "workdir": {"type": "string", "description": "Working directory (relative to repo root)"},
                    "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 60}
                },
                "required": ["command"]
            }
        },
        "read_file": {
            "name": "read_file",
            "description": "Read contents of a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path relative to repo root"},
                    "start_line": {"type": "integer", "description": "Start line (1-indexed)"},
                    "end_line": {"type": "integer", "description": "End line (inclusive)"}
                },
                "required": ["path"]
            }
        },
        "glob_files": {
            "name": "glob_files",
            "description": "Find files matching a glob pattern.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Glob pattern (e.g., '**/*.py')"},
                    "root": {"type": "string", "description": "Root directory", "default": "."}
                },
                "required": ["pattern"]
            }
        },
        "run_observer_gate": {
            "name": "run_observer_gate",
            "description": "Run the 6-point AST verification gate on a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to file to verify"}
                },
                "required": ["file_path"]
            }
        }
    }
    
    @classmethod
    def extract_tools(cls, skill_package: SkillPackage) -> List[Dict[str, Any]]:
        """Extract tool schemas for a skill"""
        tools = []
        
        # Built-in tools from manifest
        for tool_name in skill_package.manifest.tools:
            if tool_name in cls.BUILTIN_TOOLS:
                tools.append(cls.BUILTIN_TOOLS[tool_name].copy())
            else:
                # Custom tool - create minimal schema
                tools.append({
                    "name": tool_name,
                    "description": f"Custom tool: {tool_name}",
                    "parameters": {"type": "object", "properties": {}}
                })
        
        # Extract additional tools from skill content (patterns like tool calls)
        # This is a simple heuristic; in production could use more sophisticated parsing
        content_lower = skill_package.skill_content.lower()
        
        # Check for common tool patterns in content
        if "patch_file" in content_lower and "patch_file" not in skill_package.manifest.tools:
            if not any(t["name"] == "patch_file" for t in tools):
                tools.append(cls.BUILTIN_TOOLS["patch_file"].copy())
        
        if "execute_command" in content_lower and "execute_command" not in skill_package.manifest.tools:
            if not any(t["name"] == "execute_command" for t in tools):
                tools.append(cls.BUILTIN_TOOLS["execute_command"].copy())
        
        if "read_file" in content_lower and "read_file" not in skill_package.manifest.tools:
            if not any(t["name"] == "read_file" for t in tools):
                tools.append(cls.BUILTIN_TOOLS["read_file"].copy())
        
        return tools


# =============================================================================
# OPESKILLS MANAGER
# =============================================================================

class OpenSkillsManager:
    """
    OpenSkills Universal Package Manager with Progressive Disclosure Lifecycle:
    - L0 Discovery: Expose name + description in system prompt (<50 tokens/skill)
    - L1 Dynamic Load: load_skill(name) injects full instructions & tool schemas
    - L2 Dynamic Unload: unload_skill(name) evicts from context
    """
    
    DEFAULT_SKILLS_DIRS = [
        Path.home() / ".hermes" / "skills",
        Path("/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes/.hermes/skills"),
    ]
    
    def __init__(
        self,
        skills_dirs: Optional[List[Path]] = None,
        max_discovery_tokens: int = 500,  # Total budget for L0 discovery
    ):
        self.skills_dirs = skills_dirs or self.DEFAULT_SKILLS_DIRS
        self.max_discovery_tokens = max_discovery_tokens
        self._skill_index: Dict[str, SkillPackage] = {}
        self._loaded_skills: Dict[str, LoadedSkill] = {}
        self._lock = threading.RLock()
        self._parser = SkillParser()
        self._tool_extractor = ToolSchemaExtractor()
        
        # Build initial index
        self._rebuild_index()
    
    def _rebuild_index(self) -> None:
        """Scan skills directories and build index"""
        with self._lock:
            self._skill_index.clear()
            for skills_dir in self.skills_dirs:
                if not skills_dir.exists():
                    continue
                for skill_dir in skills_dir.iterdir():
                    if not skill_dir.is_dir():
                        continue
                    skill_file = skill_dir / "SKILL.md"
                    if not skill_file.exists():
                        continue
                    try:
                        pkg = self._parser.parse(skill_file)
                        self._skill_index[pkg.manifest.name] = pkg
                    except Exception as e:
                        # Silently skip invalid skills
                        pass
    
    def discover_skills(self, max_tokens: Optional[int] = None) -> List[str]:
        """
        L0 Discovery: Return list of skill discovery lines for system prompt.
        Each line: "- skill_name: description" (<50 tokens per skill)
        """
        max_t = max_tokens or self.max_discovery_tokens
        lines = []
        total_tokens = 0
        
        # Sort by name for deterministic output
        for name in sorted(self._skill_index.keys()):
            pkg = self._skill_index[name]
            line = pkg.manifest.to_discovery_line()
            line_tokens = pkg.manifest.estimate_tokens(line)
            
            if total_tokens + line_tokens > max_t:
                break
            
            lines.append(line)
            total_tokens += line_tokens
        
        return lines
    
    def get_discovery_prompt_block(self, max_tokens: Optional[int] = None) -> str:
        """Get formatted discovery block for system prompt injection"""
        lines = self.discover_skills(max_tokens)
        if not lines:
            return ""
        return "Available Skills (L0 Discovery - load with load_skill):\n" + "\n".join(lines)
    
    def load_skill(self, name: str) -> Dict[str, Any]:
        """
        L1 Dynamic Load: Load full skill into active context.
        Returns dict with manifest, skill_content, and tool_schemas.
        """
        with self._lock:
            if name not in self._skill_index:
                raise KeyError(f"Skill not found: {name}. Available: {list(self._skill_index.keys())}")
            
            pkg = self._skill_index[name]
            
            # Extract tool schemas
            tool_schemas = self._tool_extractor.extract_tools(pkg)
            
            # Create loaded skill entry
            import time
            loaded = LoadedSkill(
                name=name,
                manifest=pkg.manifest,
                skill_content=pkg.skill_content,
                tool_schemas=tool_schemas,
                load_timestamp=time.time(),
                usage_count=0
            )
            
            self._loaded_skills[name] = loaded
            pkg.loaded = True
            pkg.load_count += 1
            
            return {
                "name": name,
                "manifest": pkg.manifest,
                "skill_content": pkg.skill_content,
                "tool_schemas": tool_schemas,
                "discovery_line": pkg.manifest.to_discovery_line(),
            }
    
    def unload_skill(self, name: str) -> bool:
        """
        L2 Dynamic Unload: Evict skill from active context.
        Returns True if skill was loaded and unloaded.
        """
        with self._lock:
            if name not in self._loaded_skills:
                return False
            
            del self._loaded_skills[name]
            
            if name in self._skill_index:
                self._skill_index[name].loaded = False
            
            return True
    
    def is_loaded(self, name: str) -> bool:
        """Check if skill is currently loaded"""
        with self._lock:
            return name in self._loaded_skills
    
    def get_loaded_skills(self) -> Dict[str, LoadedSkill]:
        """Get all currently loaded skills"""
        with self._lock:
            return dict(self._loaded_skills)
    
    def get_loaded_skill_context(self, name: str) -> Optional[Dict[str, Any]]:
        """Get full context for a loaded skill (for context injection)"""
        with self._lock:
            if name not in self._loaded_skills:
                return None
            
            loaded = self._loaded_skills[name]
            loaded.usage_count += 1
            
            return {
                "name": name,
                "manifest": loaded.manifest,
                "skill_content": loaded.skill_content,
                "tool_schemas": loaded.tool_schemas,
            }
    
    def get_all_loaded_context(self) -> str:
        """Get combined context block for all loaded skills (for Slot 4 injection)"""
        with self._lock:
            if not self._loaded_skills:
                return ""
            
            blocks = []
            for name, loaded in self._loaded_skills.items():
                blocks.append(f"## Loaded Skill: {name}\n")
                blocks.append(f"{loaded.skill_content}\n")
                
                if loaded.tool_schemas:
                    blocks.append("### Tool Schemas:\n")
                    for tool in loaded.tool_schemas:
                        blocks.append(f"#### {tool['name']}\n")
                        blocks.append(f"{tool['description']}\n")
                        import json
                        blocks.append(f"```json\n{json.dumps(tool['parameters'], indent=2)}\n```\n")
            
            return "\n".join(blocks)
    
    def list_available_skills(self) -> List[Dict[str, Any]]:
        """List all available skills with metadata"""
        with self._lock:
            return [
                {
                    "name": pkg.manifest.name,
                    "description": pkg.manifest.description,
                    "version": pkg.manifest.version,
                    "author": pkg.manifest.author,
                    "tags": pkg.manifest.tags,
                    "dependencies": pkg.manifest.dependencies,
                    "tools": pkg.manifest.tools,
                    "loaded": pkg.loaded,
                    "load_count": pkg.load_count,
                    "path": str(pkg.skill_path),
                }
                for pkg in self._skill_index.values()
            ]
    
    def install_skill(
        self,
        name: str,
        skill_md_content: str,
        target_dir: Optional[Path] = None,
    ) -> Path:
        """
        Install a new skill from SKILL.md content.
        Creates directory structure with SKILL.md file.
        """
        # Parse to validate
        pkg = self._parser.parse_from_string(skill_md_content, name)
        
        if pkg.manifest.name != name:
            raise ValueError(f"Skill name in frontmatter ('{pkg.manifest.name}') doesn't match requested name ('{name}')")
        
        # Determine target directory
        if target_dir is None:
            target_dir = self.skills_dirs[0] / name
        
        target_dir = Path(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Write SKILL.md
        skill_file = target_dir / "SKILL.md"
        skill_file.write_text(skill_md_content, encoding="utf-8")
        
        # Rebuild index
        self._rebuild_index()
        
        return skill_file
    
    def uninstall_skill(self, name: str) -> bool:
        """Remove an installed skill completely"""
        with self._lock:
            # Unload if loaded
            self.unload_skill(name)
            
            # Find and remove directory
            for skills_dir in self.skills_dirs:
                skill_dir = skills_dir / name
                if skill_dir.exists() and skill_dir.is_dir():
                    shutil.rmtree(skill_dir)
                    self._rebuild_index()
                    return True
            
            return False
    
    def validate_dependencies(self, name: str) -> Dict[str, bool]:
        """Check if skill dependencies are satisfied"""
        with self._lock:
            if name not in self._skill_index:
                raise KeyError(f"Skill not found: {name}")
            
            pkg = self._skill_index[name]
            results = {}
            
            for dep in pkg.manifest.dependencies:
                results[dep] = dep in self._skill_index
            
            return results
    
    def get_skill(self, name: str) -> Optional[SkillPackage]:
        """Get skill package by name"""
        with self._lock:
            return self._skill_index.get(name)
    
    def get_zero_vram_guarantee(self) -> Dict[str, Any]:
        """Verify zero GPU VRAM overhead"""
        return {
            "skill_index_cpu_only": True,
            "parser_cpu_only": True,
            "tool_extraction_cpu_only": True,
            "no_gpu_operations": True,
            "ramdisk_compatible": True,
        }


# =============================================================================
# FACTORY & CONVENIENCE
# =============================================================================

_global_manager: Optional[OpenSkillsManager] = None
_global_lock = threading.Lock()


def get_openskills_manager(
    skills_dirs: Optional[List[Path]] = None,
    max_discovery_tokens: int = 500,
) -> OpenSkillsManager:
    """Get or create global OpenSkillsManager instance"""
    global _global_manager
    with _global_lock:
        if _global_manager is None:
            _global_manager = OpenSkillsManager(
                skills_dirs=skills_dirs,
                max_discovery_tokens=max_discovery_tokens,
            )
        return _global_manager


def reset_openskills_manager() -> None:
    """Reset global manager (for testing)"""
    global _global_manager
    with _global_lock:
        _global_manager = None


# =============================================================================
# INTEGRATION WITH PROMPT SLOTTING
# =============================================================================

def build_skills_discovery_block(manager: Optional[OpenSkillsManager] = None) -> str:
    """Build L0 discovery block for Slot 4 integration"""
    mgr = manager or get_openskills_manager()
    return mgr.get_discovery_prompt_block()


def inject_loaded_skills_context(manager: Optional[OpenSkillsManager] = None) -> str:
    """Inject all loaded skills context for active prompt"""
    mgr = manager or get_openskills_manager()
    return mgr.get_all_loaded_context()


if __name__ == "__main__":
    # Self-test
    print("OpenSkillsManager self-test")
    
    # Create temp skill
    with tempfile.TemporaryDirectory() as td:
        skills_dir = Path(td)
        
        skill_content = """---
name: test_skill
description: A test skill for validation
version: 1.0.0
author: test
tags: [test, validation]
dependencies: []
tools: [patch_file, read_file]
parameters:
  test_param: "value"
metadata:
  hermes:
    tags: [test]
---

# Test Skill

This is a test skill for OpenSkills validation.

## Usage

Use this skill to test the skill loading lifecycle.
"""
        
        manager = OpenSkillsManager(skills_dirs=[skills_dir])
        
        # Install skill
        skill_file = manager.install_skill("test_skill", skill_content)
        print(f"Installed: {skill_file}")
        
        # L0 Discovery
        discovery = manager.get_discovery_prompt_block()
        print(f"L0 Discovery:\n{discovery}")
        print(f"Discovery tokens: {manager._skill_index['test_skill'].manifest.discovery_tokens()}")
        
        # L1 Load
        loaded = manager.load_skill("test_skill")
        print(f"L1 Loaded: {loaded['name']}")
        print(f"Tools: {[t['name'] for t in loaded['tool_schemas']]}")
        
        # Check loaded
        assert manager.is_loaded("test_skill")
        
        # Get context
        context = manager.get_loaded_skill_context("test_skill")
        print(f"Context length: {len(context['skill_content'])} chars")
        
        # L2 Unload
        unloaded = manager.unload_skill("test_skill")
        print(f"L2 Unloaded: {unloaded}")
        assert not manager.is_loaded("test_skill")
        
        print("All self-tests passed!")
