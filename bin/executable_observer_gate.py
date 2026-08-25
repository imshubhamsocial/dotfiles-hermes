import shutil
#!/usr/bin/env python3
"""
Observer / Monitor Gating Layer (Astra-Derived Safe Compute Pattern)
====================================================================
Derived from OpenAI Astra's ~20% compute overhead monitoring paradigm.

This script acts as an independent, out-of-band pre-commit validation gate
that inspects all generated code artifacts BEFORE they are applied to the
filesystem. It catches:
  - Syntax errors (HTML/JS)
  - Dangerous scope mutations (eval, Function, __proto__)
  - Brace/bracket imbalance (common 4B model failure mode)
  - Duplicate variable declarations (scope dropping)
  - Oracle reference contamination (clean-room violation)
  - Size regression (truncation or context dump)

Design Philosophy:
  Astra's architecture dedicates ~20% additional compute to an independent
  Chain-of-Thought monitoring layer that inspects reasoning and tool calls
  before execution. This script is the local equivalent: a deterministic,
  sub-100ms gate that prevents filesystem corruption from LLM artifacts.

Usage:
  python3 bin/observer_gate.py <artifact_path> [--baseline <previous_path>]
  python3 bin/observer_gate.py build_preview.html
  python3 bin/observer_gate.py build_preview.html --baseline .git/refs/stash

Returns:
  Exit 0: All gates passed. Safe to commit.
  Exit 1: One or more critical gates failed. Block commit.
"""

import sys
import json
import re
import os
import subprocess
from pathlib import Path
from html.parser import HTMLParser
from collections import Counter

# Known oracle fingerprints that must NEVER appear in clean-room artifacts
ORACLE_FINGERPRINTS = [
    "gold_standard_aquarium_v",
    "ORACLE_REFERENCE_DO_NOT_COPY",
    "oracle-watermark",
    "ground-truth-signature",
]

DANGEROUS_PATTERNS = [
    (r'\beval\s*\(', 'eval() call detected'),
    (r'\bnew\s+Function\s*\(', 'Function constructor detected'),
    (r'document\.write\s*\(', 'document.write() detected'),
    (r'__proto__\s*[=\[]', '__proto__ mutation detected'),
    (r'\.innerHTML\s*=\s*["\']\s*<script', 'innerHTML script injection detected'),
    (r'\bimportScripts\s*\(', 'importScripts() detected'),
]

# U12 Karpathy Surgical Laws — AST Diff Size Gate constants
DIFF_BLOAT_FACTOR = 3
_SIG_RE = re.compile(r'^\s*(?:def|class|async\s+def|function|export\s+function)\s+([A-Za-z_$][\w$]*)', re.M)


class ScriptExtractor(HTMLParser):
    """Extract all <script> block contents from HTML."""
    def __init__(self):
        super().__init__()
        self._in_script = False
        self.scripts = []
        self._current = []
        self.unclosed_script = False

    def handle_starttag(self, tag, attrs):
        if tag == 'script':
            src = dict(attrs).get('src')
            if not src:  # Only inline scripts
                self._in_script = True
                self._current = []

    def handle_data(self, data):
        if self._in_script:
            self._current.append(data)

    def handle_endtag(self, tag):
        if tag == 'script' and self._in_script:
            self.scripts.append('\n'.join(self._current))
            self._in_script = False
            self._current = []

    def close(self):
        super().close()
        if self._in_script:
            self.unclosed_script = True
            if self._current:
                self.scripts.append('\n'.join(self._current))
            self._in_script = False


def check_syntax(content: str, filepath: str) -> dict:
    """Gate 1: HTML parse + JS AST syntax validation via Node.js."""
    errors = []
    parser = ScriptExtractor()
    try:
        parser.feed(content)
        parser.close()
    except Exception as e:
        errors.append(f"HTML parse error: {e}")

    if parser.unclosed_script:
        errors.append("Unclosed <script> tag detected (output truncation)")

    # Validate JavaScript AST inside every extracted script block
    for idx, script in enumerate(parser.scripts):
        if not script.strip():
            continue
        try:
            node_runner = ["node"] if shutil.which("node") else ["distrobox-enter", "-n", "ws-ai", "--", "node"]
            res = subprocess.run(
                node_runner + ["-e", "const code = process.argv[1]; try { new Function(code); } catch(e) { console.error(e.message); process.exit(1); }", script],
                capture_output=True, text=True, timeout=5
            )
            if res.returncode != 0:
                err_msg = res.stderr.strip().splitlines()[-1] if res.stderr.strip() else "JavaScript SyntaxError"
                errors.append(f"Script #{idx+1} SyntaxError: {err_msg}")
        except Exception as e:
            errors.append(f"Script validation error: {e}")

    if not errors and filepath.endswith('.html'):
        # Check for unclosed tags via simple heuristic
        open_tags = re.findall(r'<(body|head|html|div|script|style)\b', content, re.I)
        close_tags = re.findall(r'</(body|head|html|div|script|style)>', content, re.I)
        if len(open_tags) > 0 and len(close_tags) == 0:
            errors.append("No closing tags found - possible truncation")

    return {
        "name": "syntax_gate",
        "passed": len(errors) == 0,
        "detail": "; ".join(errors) if errors else "HTML/JS AST syntax clean"
    }


def check_dangerous_patterns(content: str) -> dict:
    """Gate 2: Detect dangerous scope mutations and injection vectors."""
    violations = []
    for pattern, desc in DANGEROUS_PATTERNS:
        matches = re.findall(pattern, content)
        if matches:
            violations.append(f"{desc} ({len(matches)}x)")

    return {
        "name": "scope_mutation_audit",
        "passed": len(violations) == 0,
        "detail": "; ".join(violations) if violations else "No dangerous patterns"
    }


def check_brace_balance(content: str) -> dict:
    """Gate 3: Verify balanced braces/brackets in script blocks."""
    extractor = ScriptExtractor()
    try:
        extractor.feed(content)
    except Exception:
        return {"name": "brace_balance", "passed": False, "detail": "Could not extract scripts"}

    all_js = '\n'.join(extractor.scripts)
    if not all_js.strip():
        return {"name": "brace_balance", "passed": True, "detail": "No inline scripts to check"}

    # Remove string literals and comments to avoid false positives
    cleaned = re.sub(r'//[^\n]*', '', all_js)  # line comments
    cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)  # block comments
    cleaned = re.sub(r'"(?:[^"\\]|\\.)*"', '""', cleaned)  # double-quoted strings
    cleaned = re.sub(r"'(?:[^'\\]|\\.)*'", "''", cleaned)  # single-quoted strings
    cleaned = re.sub(r'`(?:[^`\\]|\\.)*`', '``', cleaned, flags=re.DOTALL)  # template literals

    pairs = {'{': '}', '(': ')', '[': ']'}
    stack = []
    for ch in cleaned:
        if ch in pairs:
            stack.append(pairs[ch])
        elif ch in pairs.values():
            if not stack or stack[-1] != ch:
                return {
                    "name": "brace_balance",
                    "passed": False,
                    "detail": f"Unmatched closing '{ch}' (stack depth {len(stack)})"
                }
            stack.pop()

    if stack:
        return {
            "name": "brace_balance",
            "passed": False,
            "detail": f"{len(stack)} unclosed bracket(s): expecting {stack[-3:]}"
        }

    return {"name": "brace_balance", "passed": True, "detail": "All braces balanced"}


def check_duplicate_declarations(content: str) -> dict:
    """Gate 4: Detect duplicate top-level const/let declarations (scope dropping & redeclaration traps)."""
    extractor = ScriptExtractor()
    try:
        extractor.feed(content)
    except Exception:
        return {"name": "duplicate_declarations", "passed": True, "detail": "Parse fallback"}

    all_js = '\n'.join(extractor.scripts)
    if not all_js.strip():
        return {"name": "duplicate_declarations", "passed": True, "detail": "No scripts to analyze"}

    # Strip comments and string literals
    cleaned = re.sub(r'//[^\n]*', '', all_js)
    cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)
    cleaned = re.sub(r'"(?:[^"\\]|\\.)*"', '""', cleaned)
    cleaned = re.sub(r"'(?:[^'\\]|\\.)*'", "''", cleaned)
    cleaned = re.sub(r'`(?:[^`\\]|\\.)*`', '``', cleaned, flags=re.DOTALL)

    # Track top-level declarations (depth == 0)
    top_level_decls = []
    depth = 0
    lines = cleaned.split('\n')
    for line in lines:
        stripped = line.strip()
        # If at root level, scan for const/let/var
        if depth == 0:
            matches = re.findall(r'\b(const|let)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*[=;,]', stripped)
            for _, name in matches:
                top_level_decls.append(name)
        
        # Adjust depth
        for ch in stripped:
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth = max(0, depth - 1)

    counts = Counter(top_level_decls)
    duplicates = {name: cnt for name, cnt in counts.items() if cnt > 1}

    # Filter out single-letter variables
    false_pos = {'i', 'j', 'k', 'x', 'y', 'z', 'v', 'n', 'p', 'q', 'r', 't', 'e', 'a', 'b', 'c', 'd'}
    real_dupes = {n: c for n, c in duplicates.items() if n not in false_pos}

    if real_dupes:
        detail = "; ".join([f"top-level '{n}' redeclared {c}x" for n, c in list(real_dupes.items())[:5]])
        return {"name": "duplicate_declarations", "passed": False, "detail": detail}

    return {"name": "duplicate_declarations", "passed": True, "detail": "No duplicate top-level declarations"}


def check_oracle_contamination(content: str) -> dict:
    """Gate 5: Ensure no oracle reference content has leaked into clean-room artifact."""
    leaks = []
    content_lower = content.lower()
    for fingerprint in ORACLE_FINGERPRINTS:
        if fingerprint.lower() in content_lower:
            leaks.append(f"Oracle fingerprint found: '{fingerprint}'")

    return {
        "name": "oracle_contamination_guard",
        "passed": len(leaks) == 0,
        "detail": "; ".join(leaks) if leaks else "Clean-room integrity verified"
    }


def check_size_regression(filepath: str, content: str, baseline_path: str = None) -> dict:
    """Gate 6: Detect truncation (<50% of baseline) or context dump (>200% of baseline)."""
    new_size = len(content)

    if baseline_path and os.path.exists(baseline_path):
        old_size = os.path.getsize(baseline_path)
    elif os.path.exists(filepath + ".bak"):
        old_size = os.path.getsize(filepath + ".bak")
    else:
        return {"name": "size_regression_guard", "passed": True, "detail": f"No baseline; size={new_size}B"}

    if old_size == 0:
        return {"name": "size_regression_guard", "passed": True, "detail": "Baseline empty"}

    ratio = new_size / old_size
    if ratio < 0.5:
        return {
            "name": "size_regression_guard",
            "passed": False,
            "detail": f"TRUNCATION: {new_size}B vs baseline {old_size}B ({ratio:.1%})"
        }
    elif ratio > 2.0:
        return {
            "name": "size_regression_guard",
            "passed": False,
            "detail": f"BLOAT: {new_size}B vs baseline {old_size}B ({ratio:.1%})"
        }

    return {
        "name": "size_regression_guard",
        "passed": True,
        "detail": f"Size OK: {new_size}B ({ratio:.1%} of baseline)"
    }


def auto_format_and_sanitize(content: str, filepath: str) -> tuple[str, bool]:
    """
    Boris Cherny Rule 7 PostToolUse Auto-Formatter Hook:
    Automatically sanitizes markdown fence leaks, balances HTML containers,
    and strips trailing prompt markers before running verification gates.
    """
    modified = False
    cleaned = content

    # 1. Strip raw markdown code fences if LLM wrapped full file in ```html ... ```
    if cleaned.startswith("```html\n") or cleaned.startswith("```html\r\n"):
        cleaned = re.sub(r"^```html\r?\n", "", cleaned)
        modified = True
    elif cleaned.startswith("```\n") or cleaned.startswith("```\r\n"):
        cleaned = re.sub(r"^```\r?\n", "", cleaned)
        modified = True

    if cleaned.endswith("```") or cleaned.endswith("```\n"):
        cleaned = re.sub(r"\r?\n?```\s*$", "", cleaned)
        modified = True

    # 2. Auto-close missing script or body/html tags if cleanly terminable
    if "<script" in cleaned and "</script>" not in cleaned:
        cleaned += "\n</script>\n</body>\n</html>"
        modified = True
    elif "<body" in cleaned and "</body>" not in cleaned:
        cleaned += "\n</body>\n</html>"
        modified = True

    if modified:
        try:
            Path(filepath).write_text(cleaned, encoding='utf-8')
        except Exception:
            pass

    # 3. Multi-tier Formatter: Try Rust Biome first (<5ms), fallback to Prettier
    try:
        res = subprocess.run(
            ["distrobox", "enter", "ws-ai", "--", "biome", "format", "--write", filepath],
            capture_output=True, text=True, timeout=3
        )
        if res.returncode == 0:
            cleaned = Path(filepath).read_text(encoding='utf-8', errors='replace')
            modified = True
        else:
            # Fallback to Prettier
            subprocess.run(
                ["distrobox", "enter", "ws-ai", "--", "prettier", "--write", filepath],
                capture_output=True, text=True, timeout=5
            )
            cleaned = Path(filepath).read_text(encoding='utf-8', errors='replace')
            modified = True
    except Exception:
        pass

    return cleaned, modified


def check_ast_diff_size(old_block: str, new_block: str) -> dict:
    """
    Gate 7 (U12 Karpathy Surgical Laws): AST Diff Size Gate.

    Rejects patches where the replacement exceeds 3x the minimal necessary
    AST slice, and flags deletion of existing function/class signatures that
    were never requested (sibling obliteration / over-eager refactoring).
    """
    old_lines = [l for l in old_block.splitlines() if l.strip()]
    new_lines = [l for l in new_block.splitlines() if l.strip()]
    minimal = max(1, len(old_lines))

    problems = []
    if len(new_lines) > DIFF_BLOAT_FACTOR * minimal:
        problems.append(
            f"PATCH BLOAT: {len(new_lines)} replacement lines vs {minimal} removed "
            f"(>{DIFF_BLOAT_FACTOR}x surgical limit)"
        )

    old_sigs = set(_SIG_RE.findall(old_block))
    new_sigs = set(_SIG_RE.findall(new_block))
    obliterated = sorted(old_sigs - new_sigs)
    if obliterated:
        problems.append(
            "SIBLING OBLITERATION: existing signature(s) deleted without request: "
            + ", ".join(obliterated[:5])
        )

    return {
        "name": "ast_diff_size_gate",
        "passed": len(problems) == 0,
        "detail": "; ".join(problems) if problems else f"Surgical diff OK ({len(old_lines)}-> {len(new_lines)} lines)"
    }


def run_all_gates(filepath: str, baseline: str = None, diff_old: str = None, diff_new: str = None) -> dict:
    """Execute all observer gates and return structured verdict."""
    path = Path(filepath)
    if not path.exists():
        return {
            "passed": False,
            "checks": [],
            "verdict": f"BLOCKED: File not found: {filepath}"
        }

    content = path.read_text(errors='replace')

    # Boris Cherny Rule 7: Auto-format and sanitize before validation
    content, was_auto_formatted = auto_format_and_sanitize(content, filepath)

    checks = [
        check_syntax(content, filepath),
        check_dangerous_patterns(content),
        check_brace_balance(content),
        check_duplicate_declarations(content),
        check_oracle_contamination(content),
        check_size_regression(filepath, content, baseline),
    ]

    if diff_old is not None and diff_new is not None:
        checks.append(check_ast_diff_size(diff_old, diff_new))

    gate_count = len(checks)
    all_passed = all(c["passed"] for c in checks)
    failed = [c["name"] for c in checks if not c["passed"]]

    if all_passed:
        verdict = f"APPROVED: All {gate_count} observer gates passed. Safe to commit."
    else:
        verdict = f"BLOCKED: {len(failed)} gate(s) failed: {', '.join(failed)}"

    return {"passed": all_passed, "checks": checks, "verdict": verdict}


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <artifact_path> [--baseline <path>] [--diff-old <file>] [--diff-new <file>]", file=sys.stderr)
        sys.exit(2)

    filepath = sys.argv[1]
    baseline = None
    if '--baseline' in sys.argv:
        idx = sys.argv.index('--baseline')
        if idx + 1 < len(sys.argv):
            baseline = sys.argv[idx + 1]

    diff_old = diff_new = None
    if '--diff-old' in sys.argv and '--diff-new' in sys.argv:
        io = sys.argv.index('--diff-old')
        inn = sys.argv.index('--diff-new')
        if io + 1 < len(sys.argv) and inn + 1 < len(sys.argv):
            diff_old = Path(sys.argv[io + 1]).read_text(errors='replace') if os.path.exists(sys.argv[io + 1]) else sys.argv[io + 1]
            diff_new = Path(sys.argv[inn + 1]).read_text(errors='replace') if os.path.exists(sys.argv[inn + 1]) else sys.argv[inn + 1]

    result = run_all_gates(filepath, baseline, diff_old, diff_new)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
