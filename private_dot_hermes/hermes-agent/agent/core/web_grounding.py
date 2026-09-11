"""
Keyless Web Grounding Engine (Phase IV Core Substrate)
======================================================
Coordinates keyless multi-source search grounding (SearXNG + DDGS + Wikipedia + arXiv)
with RAMDisk caching and Search-R1 multi-turn reasoning.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

try:
    from .search_reasoner import get_search_reasoner, SearchReasoningResult
    from .fact_verifier import get_fact_verifier, FactVerificationReport
except (ImportError, ValueError):
    from search_reasoner import get_search_reasoner, SearchReasoningResult
    from fact_verifier import get_fact_verifier, FactVerificationReport


@dataclass
class GroundingResult:
    """Output contract for WebGroundingEngine."""
    executed: bool
    query: str
    grounded_response: str
    sources: List[Dict[str, Any]]
    token_estimate: int
    confidence: float
    duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class WebGroundingEngine:
    """Production web grounding engine connecting Hermes to live real-time knowledge."""

    def __init__(self):
        self.reasoner = get_search_reasoner()
        self.verifier = get_fact_verifier()

    def ground(self, query: str, policy: str = "always") -> GroundingResult:
        """
        Executes keyless web grounding for query.
        Policy: 'always' (execute search), 'cached_only', 'skip'
        """
        t0 = time.time()
        if policy == "skip":
            return GroundingResult(
                executed=False,
                query=query,
                grounded_response="",
                sources=[],
                token_estimate=0,
                confidence=1.0,
            )

        res: SearchReasoningResult = self.reasoner.reason_and_ground(query=query)
        sources_list = [s.to_dict() for s in res.sources]

        duration_ms = (time.time() - t0) * 1000

        return GroundingResult(
            executed=True,
            query=query,
            grounded_response=res.grounded_response,
            sources=sources_list,
            token_estimate=res.token_estimate,
            confidence=res.confidence_score,
            duration_ms=duration_ms,
        )

    def verify(self, claim: str) -> FactVerificationReport:
        """Verifies a factual claim against live multi-source evidence."""
        return self.verifier.verify_claim(claim)


_DEFAULT_GROUNDING_ENGINE: Optional[WebGroundingEngine] = None


def get_grounding_engine() -> WebGroundingEngine:
    global _DEFAULT_GROUNDING_ENGINE
    if _DEFAULT_GROUNDING_ENGINE is None:
        _DEFAULT_GROUNDING_ENGINE = WebGroundingEngine()
    return _DEFAULT_GROUNDING_ENGINE
