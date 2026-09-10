"""
Contract Tests for cog_verifier plugin
======================================
Verifies YAML frontmatter schema validation and vault listing for COG concepts.
"""

import tempfile
from pathlib import Path
import pytest

from plugins.cog_verifier import verify_concept, list_concepts, parse_frontmatter


def test_parse_frontmatter_valid():
    text = "---\ntitle: Test Concept\ntags: [ai, agent]\nstatus: active\n---\n\n# Body content"
    fm, body = parse_frontmatter(text)
    assert fm is not None
    assert fm["title"] == "Test Concept"
    assert fm["tags"] == ["ai", "agent"]
    assert "# Body content" in body


def test_parse_frontmatter_missing():
    text = "# Just markdown without frontmatter"
    fm, body = parse_frontmatter(text)
    assert fm is None
    assert body == text


def test_verify_concept_valid():
    with tempfile.NamedTemporaryFile(suffix=".md", mode="w", delete=False, encoding="utf-8") as f:
        f.write("---\ntitle: Verified Idea\ntags: [test]\nstatus: active\n---\n\nDetails here.")
        path = f.name

    try:
        res = verify_concept(path)
        assert res["passed"] is True
        assert res["verdict"] == "APPROVED"
        assert res["metadata"]["title"] == "Verified Idea"
    finally:
        Path(path).unlink()


def test_verify_concept_missing_fields():
    with tempfile.NamedTemporaryFile(suffix=".md", mode="w", delete=False, encoding="utf-8") as f:
        f.write("---\nstatus: active\n---\n\nDetails here.")
        path = f.name

    try:
        res = verify_concept(path)
        assert res["passed"] is False
        assert res["verdict"] == "REJECTED"
        assert "Missing required field" in res["message"]
    finally:
        Path(path).unlink()


def test_verify_existing_vault_concepts():
    concepts = list_concepts()
    assert len(concepts) >= 2
    for c in concepts:
        assert c["passed"] is True
        assert c["verdict"] == "APPROVED"
