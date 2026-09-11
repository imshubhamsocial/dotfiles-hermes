"""
Unit & Contract Tests for Proposition Verification against Python AST
=====================================================================
Validates:
1. AST ground-truth verification of classes, inheritance, parameters, and exceptions.
2. Rejection of hallucinated code claims (e.g. wrong defaults, missing exceptions).
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
import pytest


@dataclass
class AtomicProposition:
    subject: str
    predicate: str
    expected_value: any
    detail: str = ""
    verified: bool = False


class ASTPropositionVerifier:
    @classmethod
    def extract_propositions_from_ast(cls, code: str) -> list[AtomicProposition]:
        """Extracts ground-truth atomic propositions directly from code AST."""
        tree = ast.parse(code)
        extracted = []
        for n in ast.walk(tree):
            if isinstance(n, ast.ClassDef):
                extracted.append(AtomicProposition(n.name, "is_class", True))
                for b in n.bases:
                    if isinstance(b, ast.Name):
                        extracted.append(AtomicProposition(n.name, "inherits_from", b.id))
            elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                extracted.append(AtomicProposition(n.name, "is_function", True))
                for arg in n.args.args:
                    extracted.append(AtomicProposition(n.name, "has_param", arg.arg))
                if isinstance(n.returns, ast.Name):
                    extracted.append(AtomicProposition(n.name, "returns_type", n.returns.id))
        return extracted

    def verify(self, propositions: list[AtomicProposition], code: str) -> tuple[list[AtomicProposition], list[str]]:
        tree = ast.parse(code)
        errors = []

        classes = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}
        functions = {n.name: n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}

        for prop in propositions:
            if prop.predicate == "is_class":
                if prop.subject in classes:
                    prop.verified = True
                else:
                    prop.detail = f"Class {prop.subject} not found"
                    errors.append(prop.detail)

            elif prop.predicate == "inherits_from":
                cls_node = classes.get(prop.subject)
                if cls_node and any(isinstance(b, ast.Name) and b.id == prop.expected_value for b in cls_node.bases):
                    prop.verified = True
                else:
                    prop.detail = f"{prop.subject} does not inherit from {prop.expected_value}"
                    errors.append(prop.detail)

            elif prop.predicate == "is_function":
                if prop.subject in functions:
                    prop.verified = True
                else:
                    prop.detail = f"Function {prop.subject} not found"
                    errors.append(prop.detail)

            elif prop.predicate == "has_param":
                fn_node = functions.get(prop.subject)
                if fn_node and any(arg.arg == prop.expected_value for arg in fn_node.args.args):
                    prop.verified = True
                else:
                    prop.detail = f"Param {prop.expected_value} not in {prop.subject}"
                    errors.append(prop.detail)

            elif prop.predicate == "has_default":
                fn_node = functions.get(prop.subject)
                param_name, expected_val = prop.expected_value
                found = False
                if fn_node:
                    # Match defaults from the right
                    num_defaults = len(fn_node.args.defaults)
                    args_with_defaults = [a.arg for a in fn_node.args.args[-num_defaults:]]
                    if param_name in args_with_defaults:
                        idx = args_with_defaults.index(param_name)
                        default_node = fn_node.args.defaults[idx]
                        if isinstance(default_node, ast.Constant) and str(default_node.value) == str(expected_val):
                            found = True
                if found:
                    prop.verified = True
                else:
                    prop.detail = f"Default mismatch for {param_name}: expected {expected_val}"
                    errors.append(prop.detail)

            elif prop.predicate == "raises_exception":
                fn_node = functions.get(prop.subject)
                raises = []
                if fn_node:
                    for n in ast.walk(fn_node):
                        if isinstance(n, ast.Raise) and n.exc:
                            if isinstance(n.exc, ast.Call) and isinstance(n.exc.func, ast.Name):
                                raises.append(n.exc.func.id)
                            elif isinstance(n.exc, ast.Name):
                                raises.append(n.exc.id)
                if prop.expected_value in raises:
                    prop.verified = True
                else:
                    prop.detail = f"Exception mismatch: {prop.expected_value} not raised in {prop.subject}"
                    errors.append(prop.detail)

            elif prop.predicate == "returns_type":
                fn_node = functions.get(prop.subject)
                if fn_node and isinstance(fn_node.returns, ast.Name) and fn_node.returns.id == prop.expected_value:
                    prop.verified = True
                else:
                    prop.detail = f"Return type mismatch for {prop.subject}"
                    errors.append(prop.detail)

        return propositions, errors


def test_ast_verification_success():
    """Verify that propositions matching actual code AST pass verification."""
    verifier = ASTPropositionVerifier()

    code = """
class BaseManager:
    pass

class TokenBudgetManager(BaseManager):
    pass

def allocate_tokens(prompt_tokens, max_budget=2048) -> int:
    if prompt_tokens > max_budget:
        raise BudgetExceededError("Budget exceeded")
    return max_budget - prompt_tokens
"""

    propositions = [
        AtomicProposition("TokenBudgetManager", "is_class", True),
        AtomicProposition("TokenBudgetManager", "inherits_from", "BaseManager"),
        AtomicProposition("allocate_tokens", "is_function", True),
        AtomicProposition("allocate_tokens", "has_param", "prompt_tokens"),
        AtomicProposition("allocate_tokens", "has_default", ("max_budget", "2048")),
        AtomicProposition("allocate_tokens", "raises_exception", "BudgetExceededError"),
        AtomicProposition("allocate_tokens", "returns_type", "int"),
    ]

    verified_props, errors = verifier.verify(propositions, code)
    assert len(errors) == 0, f"Expected 0 errors, got: {errors}"
    assert all(p.verified for p in verified_props)


def test_ast_verification_catches_hallucination():
    """Verify that contradictory propositions (wrong default, missing exception) fail verification."""
    verifier = ASTPropositionVerifier()

    code = """
def compute_metrics(accuracy: float, threshold=0.5) -> bool:
    return accuracy >= threshold
"""

    propositions = [
        AtomicProposition("compute_metrics", "is_function", True),
        AtomicProposition("compute_metrics", "has_default", ("threshold", "0.9")),
        AtomicProposition("compute_metrics", "raises_exception", "ValueError"),
    ]

    verified_props, errors = verifier.verify(propositions, code)
    assert len(errors) == 2
    assert not verified_props[1].verified
    assert not verified_props[2].verified
    assert "Default mismatch" in verified_props[1].detail
    assert "Exception mismatch" in verified_props[2].detail



def test_ast_proposition_auto_extraction():
    code = """
class DataPipeline(BasePipeline):
    def transform(self, records) -> list:
        return [r for r in records]
"""
    props = ASTPropositionVerifier.extract_propositions_from_ast(code)
    assert any(p.subject == "DataPipeline" and p.predicate == "is_class" for p in props)
    assert any(p.subject == "DataPipeline" and p.predicate == "inherits_from" and p.expected_value == "BasePipeline" for p in props)
    assert any(p.subject == "transform" and p.predicate == "is_function" for p in props)
    assert any(p.subject == "transform" and p.predicate == "returns_type" and p.expected_value == "list" for p in props)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
