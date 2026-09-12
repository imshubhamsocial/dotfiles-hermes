"""
Ponytail Minimalist Engineering Engine & 7-Rung YAGNI Ladder
============================================================
Ingests Dietrich Gebert's "Ponytail" engineering invariant:
"The best code is the code never written. Deletion over addition. Root-cause fixes over caller-bandaids."

The 7-Rung YAGNI Ladder:
1. Does this need to be built at all? (YAGNI)
2. Does it already exist in this codebase? Reuse existing helpers.
3. Does the standard library already do this?
4. Does a native OS / platform feature cover it?
5. Does an already-installed dependency solve it?
6. Can this be one line? Make it one line.
7. Only then: write the minimum code that works.
"""

from __future__ import annotations

import ast
import inspect
import sys
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


class YAGNIRung(IntEnum):
    """The 7 rungs of the Ponytail simplicity ladder."""
    RUNG_1_YAGNI = 1           # Does it need to exist at all?
    RUNG_2_CODEBASE_REUSE = 2  # Already exists in repo?
    RUNG_3_STDLIB = 3          # Standard library covers it?
    RUNG_4_NATIVE_OS = 4       # OS / shell tool covers it?
    RUNG_5_DEPENDENCY = 5      # Installed dependency covers it?
    RUNG_6_ONE_LINE = 6        # Can be a single expression/line?
    RUNG_7_MINIMAL_CODE = 7    # Write minimum necessary code.


class BloatSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL_OVERENGINEERING = "CRITICAL_OVERENGINEERING"


@dataclass
class BloatViolation:
    rule: str
    severity: BloatSeverity
    line_number: int
    entity_name: str
    rationale: str
    simplification: str


@dataclass
class YAGNIEvaluationReport:
    """Report assessing compliance with the 7-Rung YAGNI Ladder."""
    passed: bool
    simplicity_score: float  # 0.0 (horribly bloated) to 1.0 (lean & minimal)
    assigned_rung: YAGNIRung
    violations: List[BloatViolation] = field(default_factory=list)
    remediation_notes: List[str] = field(default_factory=list)
    ast_node_count: int = 0
    lines_of_code: int = 0
    pruned_line_estimate: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "simplicity_score": round(self.simplicity_score, 3),
            "assigned_rung": int(self.assigned_rung),
            "assigned_rung_name": self.assigned_rung.name,
            "violations_count": len(self.violations),
            "violations": [
                {
                    "rule": v.rule,
                    "severity": v.severity.value,
                    "line": v.line_number,
                    "entity": v.entity_name,
                    "rationale": v.rationale,
                    "simplification": v.simplification,
                }
                for v in self.violations
            ],
            "remediation_notes": self.remediation_notes,
            "ast_node_count": self.ast_node_count,
            "lines_of_code": self.lines_of_code,
            "pruned_line_estimate": self.pruned_line_estimate,
        }


# Standard library modules commonly duplicated by over-engineered wrappers
COMMON_STDLIB_MODULES: Set[str] = {
    "pathlib", "os", "sys", "json", "sqlite3", "ast", "re", "shutil",
    "math", "hashlib", "subprocess", "itertools", "functools", "collections",
    "dataclasses", "typing", "tempfile", "glob", "time", "datetime", "uuid"
}


class PonytailDiffPruner:
    """
    AST-level inspector that enforces the 7-Rung YAGNI ladder.
    Halts unnecessary class bloat, single-method classes, wrapper passthroughs,
    and reinvented standard library routines.
    """

    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode

    def audit_code(self, source_code: str, file_context: str = "") -> YAGNIEvaluationReport:
        """
        Parses Python source code and inspects it against the Ponytail ladder.
        """
        lines = [line for line in source_code.splitlines() if line.strip() and not line.strip().startswith("#")]
        loc = len(lines)
        
        if not source_code.strip():
            return YAGNIEvaluationReport(
                passed=True,
                simplicity_score=1.0,
                assigned_rung=YAGNIRung.RUNG_1_YAGNI,
                violations=[],
                remediation_notes=["Empty code contains zero bloat."],
                ast_node_count=0,
                lines_of_code=0,
                pruned_line_estimate=0,
            )

        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            return YAGNIEvaluationReport(
                passed=False,
                simplicity_score=0.0,
                assigned_rung=YAGNIRung.RUNG_7_MINIMAL_CODE,
                violations=[
                    BloatViolation(
                        rule="syntax_error",
                        severity=BloatSeverity.CRITICAL_OVERENGINEERING,
                        line_number=e.lineno or 1,
                        entity_name="syntax",
                        rationale=f"Syntax error prevents AST parsing: {e.msg}",
                        simplification="Fix syntax before measuring complexity."
                    )
                ],
                remediation_notes=["Code fails to parse."],
                ast_node_count=0,
                lines_of_code=loc,
                pruned_line_estimate=0,
            )

        violations: List[BloatViolation] = []
        node_count = sum(1 for _ in ast.walk(tree))

        # Check 1: Single-Method Classes (God Object or Unnecessary Class Bloat)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [m for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
                # Ignore classes that inherit from Enum or BaseModel/dataclass
                is_dataclass = any(
                    (isinstance(d, ast.Name) and d.id == "dataclass") or
                    (isinstance(d, ast.Call) and isinstance(d.func, ast.Name) and d.func.id == "dataclass")
                    for d in node.decorator_list
                )
                is_enum = any(isinstance(b, ast.Name) and b.id in ("Enum", "IntEnum", "StrEnum") for b in node.bases)
                is_pydantic = any(isinstance(b, ast.Name) and b.id in ("BaseModel", "BaseSettings") for b in node.bases)

                if not (is_dataclass or is_enum or is_pydantic):
                    non_init_methods = [m for m in methods if m.name not in ("__init__", "__repr__", "__str__")]
                    if len(non_init_methods) == 1 and len(methods) <= 2:
                        violations.append(
                            BloatViolation(
                                rule="single_method_class",
                                severity=BloatSeverity.CRITICAL_OVERENGINEERING,
                                line_number=node.lineno,
                                entity_name=node.name,
                                rationale=f"Class '{node.name}' has only 1 functional method '{non_init_methods[0].name}'. In Python, a single function or lambda is more idiomatic and eliminates boilerplate.",
                                simplification=f"Replace class '{node.name}' with a top-level function '{non_init_methods[0].name}()'."
                            )
                        )

        # Check 2: Trivial Wrapper Functions (Passthroughs)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # If function body is just a single return statement calling another single function
                if len(node.body) == 1 and isinstance(node.body[0], ast.Return):
                    ret_val = node.body[0].value
                    if isinstance(ret_val, ast.Call) and isinstance(ret_val.func, ast.Name):
                        if ret_val.func.id in ("print", "len", "open", "str", "int", "list", "dict", "set"):
                            violations.append(
                                BloatViolation(
                                    rule="trivial_builtin_wrapper",
                                    severity=BloatSeverity.WARNING,
                                    line_number=node.lineno,
                                    entity_name=node.name,
                                    rationale=f"Function '{node.name}' trivially wraps built-in '{ret_val.func.id}()'. Caller should call built-in directly (Rung 3: Standard Library).",
                                    simplification=f"Inline the call to '{ret_val.func.id}()' at call sites."
                                )
                            )

        # Check 3: Redundant custom file reading/writing classes
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                lower_name = node.name.lower()
                if any(kw in lower_name for kw in ("filereader", "filewriter", "filehelper", "iomanager", "pathhelper")):
                    violations.append(
                        BloatViolation(
                            rule="reinventing_pathlib",
                            severity=BloatSeverity.CRITICAL_OVERENGINEERING,
                            line_number=node.lineno,
                            entity_name=node.name,
                            rationale=f"Class '{node.name}' reimplements file IO helpers covered natively by standard library 'pathlib.Path' (Rung 3: Standard Library).",
                            simplification="Use pathlib.Path(path).read_text() or write_text() directly."
                        )
                    )

        # Calculate simplicity score
        # Base score 1.0, minus 0.35 per critical violation, minus 0.15 per warning
        score_deductions = 0.0
        pruned_lines = 0
        for v in violations:
            if v.severity == BloatSeverity.CRITICAL_OVERENGINEERING:
                score_deductions += 0.35
                pruned_lines += 15
            elif v.severity == BloatSeverity.WARNING:
                score_deductions += 0.15
                pruned_lines += 5

        simplicity_score = max(0.0, 1.0 - score_deductions)
        passed = (simplicity_score >= 0.70) if self.strict_mode else (simplicity_score >= 0.50)

        # Assigned rung
        if loc <= 1 and node_count <= 5:
            assigned_rung = YAGNIRung.RUNG_6_ONE_LINE
        elif not violations and loc < 25:
            assigned_rung = YAGNIRung.RUNG_7_MINIMAL_CODE
        elif any(v.rule == "reinventing_pathlib" for v in violations):
            assigned_rung = YAGNIRung.RUNG_3_STDLIB
        else:
            assigned_rung = YAGNIRung.RUNG_7_MINIMAL_CODE

        notes = []
        if violations:
            notes.append(f"Detected {len(violations)} over-engineering violation(s).")
            for v in violations:
                notes.append(f"Line {v.line_number}: {v.simplification}")
        else:
            notes.append("Code strictly conforms to the 7-Rung YAGNI Ladder.")

        return YAGNIEvaluationReport(
            passed=passed,
            simplicity_score=simplicity_score,
            assigned_rung=assigned_rung,
            violations=violations,
            remediation_notes=notes,
            ast_node_count=node_count,
            lines_of_code=loc,
            pruned_line_estimate=min(loc, pruned_lines),
        )


class PonytailLadder:
    """
    Evaluates requirements and proposed design choices against the 7 rungs.
    """

    @staticmethod
    def evaluate_intent(
        requirement: str,
        existing_symbols: Optional[List[str]] = None,
        installed_packages: Optional[List[str]] = None,
    ) -> Tuple[YAGNIRung, str]:
        """
        Determine the lowest sufficient rung on the ladder to satisfy a requirement.
        """
        req_lower = requirement.lower()
        existing_symbols = existing_symbols or []
        installed_packages = installed_packages or []

        import re
        words = set(re.findall(r"\b\w+\b", req_lower))

        # Rung 1: YAGNI
        if any(w in req_lower for w in ("mock future", "just in case", "might need later", "overkill", "speculative")):
            return (
                YAGNIRung.RUNG_1_YAGNI,
                "Requirement is speculative or gold-plating. Do not build."
            )

        # Rung 2: Codebase Reuse
        for sym in existing_symbols:
            if sym.lower() in words or any(part in words for part in sym.lower().split("_") if len(part) > 3):
                return (
                    YAGNIRung.RUNG_2_CODEBASE_REUSE,
                    f"Requirement can be satisfied by reusing existing helper/symbol '{sym}'."
                )

        # Rung 3: Standard Library
        stdlib_matches = [m for m in COMMON_STDLIB_MODULES if m in words]
        if stdlib_matches or any(k in req_lower for k in ("read file", "write file", "parse json", "sqlite", "path manipulation")):
            match_name = stdlib_matches[0] if stdlib_matches else "pathlib/json/sqlite3"
            return (
                YAGNIRung.RUNG_3_STDLIB,
                f"Standard library '{match_name}' covers this requirement natively. Zero external code needed."
            )

        # Rung 4: Native OS
        if any(k in words for k in ("diff", "grep", "curl", "tar", "find", "archive", "podman", "docker", "bwrap")) or any(k in req_lower for k in ("find files", "process list", "shell command")):
            return (
                YAGNIRung.RUNG_4_NATIVE_OS,
                "Native OS utilities / shell commands cover this directly."
            )

        # Rung 5: Installed Dependency
        for pkg in installed_packages:
            if pkg.lower() in req_lower:
                return (
                    YAGNIRung.RUNG_5_DEPENDENCY,
                    f"Already-installed dependency '{pkg}' covers this requirement."
                )

        # Rung 6: Single-Line
        if any(k in req_lower for k in ("filter", "map", "count", "sum", "extract list", "transform dict")):
            return (
                YAGNIRung.RUNG_6_ONE_LINE,
                "Expressible as a single-line list/dict comprehension or generator expression."
            )

        # Rung 7: Minimal Working Code
        return (
            YAGNIRung.RUNG_7_MINIMAL_CODE,
            "Proceed with minimal implementation adhering strictly to root-cause fixes and minimal diffs."
        )


class DiffAuditReport:
    """Report assessing AST diff size, redundant helpers, dependencies, and root-cause invariants."""
    def __init__(
        self,
        passed: bool,
        verdict: str,
        diff_ratio: float,
        old_loc: int,
        new_loc: int,
        violations: List[BloatViolation],
        redundant_helpers: List[str],
        unrequested_dependencies: List[str],
        root_cause_passed: bool,
        remediation_notes: List[str],
    ):
        self.passed = passed
        self.verdict = verdict
        self.diff_ratio = diff_ratio
        self.old_loc = old_loc
        self.new_loc = new_loc
        self.violations = violations
        self.redundant_helpers = redundant_helpers
        self.unrequested_dependencies = unrequested_dependencies
        self.root_cause_passed = root_cause_passed
        self.remediation_notes = remediation_notes

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "verdict": self.verdict,
            "diff_ratio": round(self.diff_ratio, 2),
            "old_loc": self.old_loc,
            "new_loc": self.new_loc,
            "violations_count": len(self.violations),
            "violations": [
                {
                    "rule": v.rule,
                    "severity": v.severity.value,
                    "line": v.line_number,
                    "entity": v.entity_name,
                    "rationale": v.rationale,
                    "simplification": v.simplification,
                }
                for v in self.violations
            ],
            "redundant_helpers": self.redundant_helpers,
            "unrequested_dependencies": self.unrequested_dependencies,
            "root_cause_passed": self.root_cause_passed,
            "remediation_notes": self.remediation_notes,
        }


def _extract_imports(tree: ast.AST) -> Set[str]:
    """Extract top-level module names imported in AST."""
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".")[0])
    return imports


def _extract_signatures(tree: ast.AST) -> Set[str]:
    """Extract top-level functions and classes defined in AST."""
    sigs = set()
    for node in getattr(tree, "body", []):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            sigs.add(node.name)
    return sigs


# Known comprehensive standard library names (Python 3.10-3.14)
STANDARD_LIBRARY_NAMES: Set[str] = COMMON_STDLIB_MODULES.union({
    "abc", "argparse", "array", "asyncio", "base64", "binascii", "builtins",
    "bz2", "calendar", "cmath", "code", "codecs", "concurrent", "contextlib",
    "contextvars", "copy", "csv", "ctypes", "datetime", "decimal", "difflib",
    "dis", "doctest", "email", "enum", "errno", "faulthandler", "filecmp",
    "fileinput", "fnmatch", "fractions", "ftplib", "functools", "gc", "getopt",
    "getpass", "gettext", "glob", "gzip", "hashlib", "heapq", "hmac", "html",
    "http", "idlelib", "imaplib", "importlib", "inspect", "io", "ipaddress",
    "itertools", "json", "keyword", "linecache", "locale", "logging", "lzma",
    "math", "mimetypes", "mmap", "modulefinder", "multiprocessing", "netrc",
    "numbers", "operator", "optparse", "os", "pathlib", "pdb", "pickle",
    "pkgutil", "platform", "plistlib", "poplib", "posix", "pprint", "profile",
    "pstats", "pty", "pwd", "queue", "quopri", "random", "re", "readline",
    "reprlib", "resource", "rlcompleter", "sched", "secrets", "select",
    "selectors", "shelve", "shlex", "shutil", "signal", "site", "smtplib",
    "socket", "socketserver", "sqlite3", "ssl", "stat", "statistics", "string",
    "stringprep", "struct", "subprocess", "sys", "sysconfig", "syslog", "tarfile",
    "telnetlib", "tempfile", "termios", "textwrap", "threading", "time",
    "timeit", "tkinter", "token", "tokenize", "trace", "traceback", "tracemalloc",
    "tty", "types", "typing", "unicodedata", "unittest", "urllib", "uuid",
    "venv", "warnings", "wave", "weakref", "webbrowser", "xml", "xmlrpc",
    "zipapp", "zipfile", "zipimport", "zlib", "zoneinfo"
})


# Extend PonytailDiffPruner
def audit_diff(
    self,
    old_code: str,
    new_code: str,
    requested_dependencies: Optional[List[str]] = None,
    call_graph: Optional[Dict[str, List[str]]] = None,
    failing_symbol: Optional[str] = None,
) -> DiffAuditReport:
    """
    Evaluates a proposed code patch against the Ponytail Minimalist Invariants:
    1. AST Diff Size (flags bloat if new LOC > 3x old LOC on non-trivial replacements).
    2. Sibling Signature Obliteration (flags deletions of unrequested existing symbols).
    3. Redundant Helper Functions (flags unnecessary passthroughs and single-caller wrappers).
    4. Unrequested Dependencies (flags third-party libraries not requested).
    5. Root-Cause Divergence Invariant (ensures fixes target root callee rather than caller band-aids).
    """
    old_lines = [l for l in old_code.splitlines() if l.strip() and not l.strip().startswith("#")]
    new_lines = [l for l in new_code.splitlines() if l.strip() and not l.strip().startswith("#")]
    old_loc = len(old_lines)
    new_loc = len(new_lines)
    diff_ratio = (new_loc / max(1, old_loc))

    violations: List[BloatViolation] = []
    redundant_helpers: List[str] = []
    unrequested_deps: List[str] = []
    root_cause_passed = True
    notes: List[str] = []

    # Parse ASTs
    old_tree = None
    new_tree = None
    try:
        if old_code.strip():
            old_tree = ast.parse(old_code)
    except SyntaxError:
        pass

    try:
        if new_code.strip():
            new_tree = ast.parse(new_code)
    except SyntaxError as e:
        violations.append(
            BloatViolation(
                rule="syntax_error",
                severity=BloatSeverity.CRITICAL_OVERENGINEERING,
                line_number=e.lineno or 1,
                entity_name="syntax",
                rationale=f"Replacement code fails syntax validation: {e.msg}",
                simplification="Fix syntax errors before submitting patch."
            )
        )

    # 1. AST Diff Size Gate (U12 Karpathy Surgical Limit: 3x bloat factor)
    if old_loc >= 2 and new_loc > 3 * old_loc and (new_loc - old_loc) >= 5:
        violations.append(
            BloatViolation(
                rule="ast_diff_bloat",
                severity=BloatSeverity.CRITICAL_OVERENGINEERING,
                line_number=1,
                entity_name="diff_size",
                rationale=f"Replacement size ({new_loc} LOC) exceeds 3x original size ({old_loc} LOC) — ratio {diff_ratio:.1f}x exceeds surgical limit.",
                simplification="Apply minimal surgical patch to modified logic only."
            )
        )
        notes.append(f"Diff bloat detected: {new_loc} LOC vs {old_loc} LOC.")

    # 2. Sibling Signature Obliteration
    if old_tree and new_tree:
        old_sigs = _extract_signatures(old_tree)
        new_sigs = _extract_signatures(new_tree)
        deleted_sigs = old_sigs - new_sigs
        if deleted_sigs:
            violations.append(
                BloatViolation(
                    rule="sibling_obliteration",
                    severity=BloatSeverity.CRITICAL_OVERENGINEERING,
                    line_number=1,
                    entity_name=", ".join(sorted(deleted_sigs)),
                    rationale=f"Existing definition(s) obliterated without explicit request: {', '.join(sorted(deleted_sigs))}",
                    simplification="Preserve existing non-targeted functions and classes in scope."
                )
            )

    # 3. Redundant Helper Functions & Passthroughs
    if new_tree:
        old_sigs = _extract_signatures(old_tree) if old_tree else set()
        for node in getattr(new_tree, "body", []):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name not in old_sigs:
                    # Check if body is trivial passthrough wrapper
                    if len(node.body) == 1 and isinstance(node.body[0], ast.Return):
                        ret = node.body[0].value
                        if isinstance(ret, ast.Call) and isinstance(ret.func, ast.Name):
                            redundant_helpers.append(node.name)
                            violations.append(
                                BloatViolation(
                                    rule="redundant_helper_function",
                                    severity=BloatSeverity.CRITICAL_OVERENGINEERING,
                                    line_number=node.lineno,
                                    entity_name=node.name,
                                    rationale=f"New helper '{node.name}' is a redundant 1-line wrapper around '{ret.func.id}()'. Inline directly at call site (YAGNI Rung 6).",
                                    simplification=f"Inline call to '{ret.func.id}' directly."
                                )
                            )

    # 4. Unrequested Dependencies Gate
    if new_tree:
        old_imports = _extract_imports(old_tree) if old_tree else set()
        new_imports = _extract_imports(new_tree)
        introduced_imports = new_imports - old_imports
        allowed_reqs = set(requested_dependencies or [])

        for imp in introduced_imports:
            # Check if in standard library or explicitly requested
            if imp not in STANDARD_LIBRARY_NAMES and imp not in allowed_reqs:
                unrequested_deps.append(imp)
                violations.append(
                    BloatViolation(
                        rule="unrequested_dependency",
                        severity=BloatSeverity.CRITICAL_OVERENGINEERING,
                        line_number=1,
                        entity_name=imp,
                        rationale=f"Introduced unrequested external dependency '{imp}'. Violates YAGNI Rung 5.",
                        simplification=f"Use standard library or existing dependencies instead of importing '{imp}'."
                    )
                )

    # 5. Root-Cause Divergence Invariant (Call Graph Analysis)
    if failing_symbol and call_graph and old_tree and new_tree:
        # call_graph maps root_callee -> list of callers
        # If failing_symbol is root_callee, the patch should modify failing_symbol itself,
        # NOT just modify callers to wrap calls with defensive checks.
        callers = call_graph.get(failing_symbol, [])
        if callers:
            old_sigs = _extract_signatures(old_tree)
            new_sigs = _extract_signatures(new_tree)
            # Check if root symbol was modified in the patch
            root_modified = False
            callers_modified = set()

            # Inspect function body changes
            old_funcs = {n.name: n for n in getattr(old_tree, "body", []) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
            new_funcs = {n.name: n for n in getattr(new_tree, "body", []) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}

            if failing_symbol in new_funcs:
                old_f = old_funcs.get(failing_symbol)
                new_f = new_funcs.get(failing_symbol)
                if old_f and ast.dump(old_f) != ast.dump(new_f):
                    root_modified = True

            for c in callers:
                if c in new_funcs and c in old_funcs:
                    if ast.dump(old_funcs[c]) != ast.dump(new_funcs[c]):
                        callers_modified.add(c)

            if callers_modified and not root_modified:
                root_cause_passed = False
                violations.append(
                    BloatViolation(
                        rule="caller_bandaid_divergence",
                        severity=BloatSeverity.CRITICAL_OVERENGINEERING,
                        line_number=1,
                        entity_name=failing_symbol,
                        rationale=(
                            f"Patch modifies caller(s) {sorted(callers_modified)} with defensive checks rather than "
                            f"remediating the root-cause failure at earliest point of divergence: '{failing_symbol}'."
                        ),
                        simplification=f"Refactor and fix '{failing_symbol}' directly instead of wrapping call sites."
                    )
                )
                notes.append(f"Root-cause invariant failure: patched callers {sorted(callers_modified)} instead of root '{failing_symbol}'.")

    # Overall verdict
    critical_count = sum(1 for v in violations if v.severity == BloatSeverity.CRITICAL_OVERENGINEERING)
    passed = (critical_count == 0) and root_cause_passed
    verdict = "APPROVED" if passed else "REJECTED"

    if passed:
        notes.append("Diff strictly passes all Ponytail Minimalist and Anti-Overengineering Gates.")

    return DiffAuditReport(
        passed=passed,
        verdict=verdict,
        diff_ratio=diff_ratio,
        old_loc=old_loc,
        new_loc=new_loc,
        violations=violations,
        redundant_helpers=redundant_helpers,
        unrequested_dependencies=unrequested_deps,
        root_cause_passed=root_cause_passed,
        remediation_notes=notes,
    )

# Attach method to PonytailDiffPruner
PonytailDiffPruner.audit_diff = audit_diff


def pre_commit_observer_gate(
    old_code: str,
    new_code: str,
    filepath: str = "",
    requested_dependencies: Optional[List[str]] = None,
    call_graph: Optional[Dict[str, List[str]]] = None,
    failing_symbol: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Pre-commit observer gate computing AST diff size, detecting redundant helpers,
    rejecting unrequested dependencies, and enforcing root-cause call graph invariants.
    """
    pruner = PonytailDiffPruner(strict_mode=True)
    report = pruner.audit_diff(
        old_code=old_code,
        new_code=new_code,
        requested_dependencies=requested_dependencies,
        call_graph=call_graph,
        failing_symbol=failing_symbol,
    )

    checks = [
        {
            "name": "ast_diff_size_gate",
            "passed": not any(v.rule == "ast_diff_bloat" for v in report.violations),
            "detail": f"Diff ratio {report.diff_ratio:.2f}x ({report.old_loc} LOC -> {report.new_loc} LOC)",
        },
        {
            "name": "sibling_preservation_gate",
            "passed": not any(v.rule == "sibling_obliteration" for v in report.violations),
            "detail": "Existing non-targeted definitions preserved",
        },
        {
            "name": "redundant_helper_gate",
            "passed": len(report.redundant_helpers) == 0,
            "detail": f"{len(report.redundant_helpers)} redundant helper(s) detected" if report.redundant_helpers else "No redundant helpers introduced",
        },
        {
            "name": "unrequested_dependencies_gate",
            "passed": len(report.unrequested_dependencies) == 0,
            "detail": f"Unrequested: {report.unrequested_dependencies}" if report.unrequested_dependencies else "Dependencies clean (YAGNI Rung 5 passed)",
        },
        {
            "name": "root_cause_invariant_gate",
            "passed": report.root_cause_passed,
            "detail": "Fix applied at earliest point of divergence" if report.root_cause_passed else "Superficial caller-wrapping band-aid rejected",
        },
    ]

    all_passed = report.passed and all(c["passed"] for c in checks)
    verdict = "APPROVED" if all_passed else "REJECTED"

    return {
        "passed": all_passed,
        "verdict": verdict,
        "filepath": filepath,
        "checks": checks,
        "report": report.to_dict(),
    }


_DEFAULT_PRUNER = PonytailDiffPruner()

def audit_code_simplicity(code: str, strict: bool = True) -> YAGNIEvaluationReport:
    """Convenience helper to audit code against the 7-Rung YAGNI Ladder."""
    pruner = _DEFAULT_PRUNER if strict else PonytailDiffPruner(strict_mode=False)
    return pruner.audit_code(code)

