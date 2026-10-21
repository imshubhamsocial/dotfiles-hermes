#!/usr/bin/env python3.13
# File: .hermes/skill_evaluator.py — Deterministic Skill & Zero-Dead-Ends Evaluator
import ast
import importlib.util
import re
import sys
from pathlib import Path

HERMES_HOME = Path(__file__).resolve().parent
SKILLS_DIR = HERMES_HOME / "skills"


def evaluate_all_skills() -> dict:
    errors: list[str] = []
    skills_checked = 0

    for item in sorted(HERMES_HOME.rglob("*")):
        if "hermes-agent" in item.parts or ".venv" in item.parts or "cache" in item.parts:
            continue
        if item.is_symlink() and not item.exists():
            errors.append(f"BROKEN_SYMLINK: {item} -> {item.readlink()}")

    for skill_md in sorted(SKILLS_DIR.rglob("SKILL.md")):
        skills_checked += 1
        content = skill_md.read_text(encoding="utf-8", errors="ignore")
        if skill_md.parent.name.startswith("phase") or skill_md.parent.parent == SKILLS_DIR:
            fm_match = re.match(r"^---\n(.*?)\n---", content, flags=re.DOTALL)
            if not fm_match:
                errors.append(f"MISSING_FRONTMATTER: {skill_md}")
            else:
                fm_raw = fm_match.group(1)
                if len(fm_raw.encode("utf-8")) > 200:
                    errors.append(f"FRONTMATTER_OVER_200B ({len(fm_raw)}B): {skill_md}")
                desc_match = re.search(r"^description:\s*['\"]?(.*?)['\"]?\s*$", fm_raw, re.MULTILINE)
                if desc_match and len(desc_match.group(1).strip()) > 40:
                    errors.append(f"DESC_OVER_40_CHARS ({len(desc_match.group(1))}c): {skill_md}")

    for py_file in sorted(HERMES_HOME.rglob("*.py")):
        if "hermes-agent" in py_file.parts or ".venv" in py_file.parts or "cache" in py_file.parts or "scripts" in py_file.parts:
            continue
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8", errors="ignore"), filename=str(py_file))
        except SyntaxError as exc:
            errors.append(f"SYNTAX_ERROR: {py_file}: {exc}")
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top_pkg = alias.name.split(".")[0]
                    if top_pkg not in sys.stdlib_module_names and importlib.util.find_spec(top_pkg) is None:
                        errors.append(f"BROKEN_IMPORT ({top_pkg}): {py_file}:{node.lineno}")

    return {"skills_checked": skills_checked, "dead_ends_found": len(errors), "errors": errors}


if __name__ == "__main__":
    report = evaluate_all_skills()
    print(f"Skills Audited: {report['skills_checked']} | Dead Ends: {report['dead_ends_found']}")
    if report["errors"]:
        for err in report["errors"]:
            print(f"  [!] {err}", file=sys.stderr)
        sys.exit(1)
    sys.exit(0)
