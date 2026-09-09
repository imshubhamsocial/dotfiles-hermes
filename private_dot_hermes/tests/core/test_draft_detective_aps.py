"""
Unit & Contract Tests for Gemma-APS (Abstractive Proposition Segmentation) in DraftDetective
===========================================================================================
Validates:
1. Proposition segmentation from prose summaries (signatures, defaults, returns, exceptions, classes)
2. AST ground-truth verification against Python code diffs
3. Rejection of contradictory / hallucinated propositions (e.g. default value or exception mismatches)
4. Integration into full_pre_commit_audit with zero GPU VRAM impact
"""

import ast
from pathlib import Path
import pytest

from hermes_core.draft_detective import (
    AtomicProposition,
    PropositionSegmenter,
    ASTPropositionVerifier,
    DraftDetective,
    create_draft_detective,
)


def test_gemma_aps_proposition_segmentation():
    """Verify Gemma-APS decomposes technical assertions into atomic propositions."""
    segmenter = PropositionSegmenter()

    text = """
    I have added class `TokenBudgetManager(BaseManager)` to handle limits.
    Implemented function `allocate_tokens(prompt_tokens, max_budget=2048)` which returns int and raises BudgetExceededError when full.
    """

    props = segmenter.segment_text(text)
    assert len(props) >= 5

    # Check class and inheritance propositions
    cls_props = [p for p in props if p.subject == "TokenBudgetManager"]
    assert any(p.predicate == "is_class" for p in cls_props)
    assert any(p.predicate == "inherits_from" and p.expected_value == "BaseManager" for p in cls_props)

    # Check function propositions
    fn_props = [p for p in props if p.subject == "allocate_tokens"]
    assert any(p.predicate == "is_function" for p in fn_props)
    assert any(p.predicate == "has_param" and p.expected_value == "prompt_tokens" for p in fn_props)
    assert any(p.predicate == "has_default" and p.expected_value == ("max_budget", "2048") for p in fn_props)
    assert any(p.predicate == "raises_exception" and p.expected_value == "BudgetExceededError" for p in fn_props)
    assert any(p.predicate == "returns_type" and p.expected_value == "int" for p in fn_props)


def test_gemma_aps_ast_verification_success():
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
        AtomicProposition("TokenBudgetManager", "is_class", True, ""),
        AtomicProposition("TokenBudgetManager", "inherits_from", "BaseManager", ""),
        AtomicProposition("allocate_tokens", "is_function", True, ""),
        AtomicProposition("allocate_tokens", "has_param", "prompt_tokens", ""),
        AtomicProposition("allocate_tokens", "has_default", ("max_budget", "2048"), ""),
        AtomicProposition("allocate_tokens", "raises_exception", "BudgetExceededError", ""),
        AtomicProposition("allocate_tokens", "returns_type", "int", ""),
    ]

    verified_props, errors = verifier.verify(propositions, code)
    assert len(errors) == 0, f"Expected 0 errors, got: {errors}"
    assert all(p.verified for p in verified_props)


def test_gemma_aps_ast_verification_catches_hallucination():
    """Verify that contradictory propositions (wrong default, missing exception) fail verification."""
    verifier = ASTPropositionVerifier()

    code = """
def compute_metrics(accuracy: float, threshold=0.5) -> bool:
    return accuracy >= threshold
"""

    # Claim asserts threshold=0.9 and raises ValueError (both false in AST)
    propositions = [
        AtomicProposition("compute_metrics", "is_function", True, ""),
        AtomicProposition("compute_metrics", "has_default", ("threshold", "0.9"), "Asserted 0.9 default"),
        AtomicProposition("compute_metrics", "raises_exception", "ValueError", "Asserted raises ValueError"),
    ]

    verified_props, errors = verifier.verify(propositions, code)
    assert len(errors) == 2
    assert not verified_props[1].verified
    assert not verified_props[2].verified
    assert "Default mismatch" in verified_props[1].detail
    assert "Exception mismatch" in verified_props[2].detail


def test_gemma_aps_full_pre_commit_audit():
    """Verify full pre-commit gate rejects code diff when markdown makes contradictory claims."""
    dd = create_draft_detective()

    summary_clean = "Implemented `process_batch(items, batch_size=32)` which raises BatchError."
    code_matching = """
def process_batch(items, batch_size=32):
    if not items:
        raise BatchError("Empty")
    return len(items)
"""
    # 1. Matching audit passes
    report_pass = dd.full_pre_commit_audit(summary_clean, code_matching)
    assert report_pass.approved is True
    assert report_pass.verified_propositions >= 2
    assert report_pass.failed_propositions == 0

    # 2. Contradictory audit fails (claimed batch_size=64, but code has 32)
    summary_contradictory = "Implemented `process_batch(items, batch_size=64)` which raises BatchError."
    report_fail = dd.full_pre_commit_audit(summary_contradictory, code_matching)
    assert report_fail.approved is False
    assert report_fail.failed_propositions >= 1
    assert any("Default mismatch" in h for h in report_fail.hallucinations)
