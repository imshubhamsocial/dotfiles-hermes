"""
Real-Time Fact Verifier (Phase IV.3)
=====================================
Validates factual claims against independent real-time search backends:
  - Input: claim string
  - Process: Search 3 sources, check consistency
  - Output: {claim, verified: bool, confidence: float, sources: [], rationale: str}
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

try:
    from .search_reasoner import get_search_reasoner, SearchResult
except (ImportError, ValueError):
    from search_reasoner import get_search_reasoner, SearchResult


@dataclass
class FactVerificationReport:
    """Standardized outcome of fact verification inquiry."""
    claim: str
    verified: bool
    confidence: float
    agreement_count: int
    sources: List[Dict[str, Any]]
    rationale: str
    duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RealTimeFactVerifier:
    """
    Engine that verifies claims against multi-source evidence.
    Extracts key entity n-grams and numerical anchors, queries backends,
    and calculates empirical cross-source agreement.
    """

    def __init__(self):
        self.reasoner = get_search_reasoner()

    def extract_claim_anchors(self, claim: str) -> List[str]:
        """Extracts essential named entities, numbers, and nouns from the claim."""
        anchors = []
        # Extract numbers, dates, or measurements
        nums = re.findall(r"\b\d+(?:[\.,]\d+)?(?:\s*[a-zA-Z%]+)?\b", claim)
        anchors.extend(nums)

        # Extract capitalized entities or acronyms
        caps = re.findall(r"\b[A-Z][a-zA-Z0-9_-]+\b", claim)
        anchors.extend(caps)

        # Significant words
        clean = re.sub(r"[^\w\s]", " ", claim).lower()
        words = [w for w in clean.split() if len(w) >= 4 and w not in (
            "that", "with", "from", "this", "they", "have", "were", "been", "about"
        )]
        anchors.extend(words[:5])

        return list(set(anchors))

    def verify_claim(self, claim: str, min_sources: int = 2) -> FactVerificationReport:
        """Verifies a single factual claim against multi-source search evidence."""
        t0 = time.time()
        anchors = self.extract_claim_anchors(claim)

        # 1. Dispatch multi-source query
        search_query = f"{claim.strip()}"
        sources = self.reasoner.dispatch_search(search_query, max_results=6)
        if not sources:
            time.sleep(0.5)
            sources = self.reasoner.dispatch_search(search_query, max_results=6)

        # If sparse, try searching the primary anchor keywords
        if len(sources) < 2 and anchors:
            fallback_q = " ".join(anchors[:4])
            extra = self.reasoner.dispatch_search(fallback_q, max_results=4)
            sources.extend(extra)

        # 2. Check corroboration & consistency
        agreeing_sources: List[Dict[str, Any]] = []
        claim_words = set(re.findall(r"\b[a-zA-Z0-9]{3,}\b", claim.lower()))
        # Identify discriminating anchors: numbers, years, capitalized entities
        critical_anchors = [a.lower() for a in anchors if any(c.isdigit() for c in a) or (len(a) >= 4 and a.lower() not in ("were", "been", "from", "with", "that", "this"))]

        for s in sources:
            combined_text = (s.title + " " + s.snippet).lower()
            snippet_words = set(re.findall(r"\b[a-zA-Z0-9]{3,}\b", combined_text))

            # Measure overlap with claim key concepts
            common = claim_words.intersection(snippet_words)
            overlap_ratio = len(common) / len(claim_words) if claim_words else 0.0

            # If claim has critical discriminating anchors, check that the majority are present
            critical_match = True
            numeric_anchors = [w.lower() for w in re.findall(r"\b\d+\b", claim)]
            if numeric_anchors and not all(na in combined_text for na in numeric_anchors):
                critical_match = False

            if critical_match and critical_anchors:
                matched_critical = sum(1 for ca in critical_anchors if ca in combined_text)
                if matched_critical / len(critical_anchors) < 0.70:
                    critical_match = False

            if overlap_ratio >= 0.50 and critical_match:
                agreeing_sources.append({
                    "title": s.title,
                    "url": s.url,
                    "snippet": s.snippet[:250],
                    "source_type": s.source_type,
                    "overlap_ratio": round(overlap_ratio, 3),
                })

        # 3. Formulate verdict
        agreement_count = len(agreeing_sources)
        if agreement_count >= min_sources:
            verified = True
            confidence = min(0.98, 0.70 + (0.07 * agreement_count))
            rationale = f"Corroborated across {agreement_count} independent sources with high concept overlap."
        elif agreement_count == 1:
            verified = True
            confidence = 0.65
            rationale = "Partially corroborated by 1 primary source. Further cross-verification recommended."
        else:
            verified = False
            confidence = 0.25
            rationale = "No independent sources corroborated the factual claim."

        duration_ms = (time.time() - t0) * 1000

        return FactVerificationReport(
            claim=claim,
            verified=verified,
            confidence=confidence,
            agreement_count=agreement_count,
            sources=agreeing_sources[:5],
            rationale=rationale,
            duration_ms=duration_ms,
        )


_DEFAULT_VERIFIER: Optional[RealTimeFactVerifier] = None


def get_fact_verifier() -> RealTimeFactVerifier:
    global _DEFAULT_VERIFIER
    if _DEFAULT_VERIFIER is None:
        _DEFAULT_VERIFIER = RealTimeFactVerifier()
    return _DEFAULT_VERIFIER


def verify_claim(claim: str) -> FactVerificationReport:
    """One-line entrypoint for verifying any factual proposition."""
    return get_fact_verifier().verify_claim(claim)
