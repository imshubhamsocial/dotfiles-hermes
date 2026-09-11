"""
Mixture-of-Agents (MoA) Consensus & Quorum Audit Engine (Phase III.1)
=====================================================================
Based on arXiv:2406.04692 (Mixture-of-Agents Enhances LLM Capabilities).
Implements a two-layer collaborative intelligence system:
  1. Proposer Layer: 3 concurrent Hermes instances with specialized complementary prompts
     - Instance A: Reasoning-focused analytical prompt (temp 0.1)
     - Instance B: Creativity & lateral exploration prompt (temp 0.7)
     - Instance C: Red-team adversarial critic prompt (temp 0.1)
  2. Scoring & Consensus:
     - Per-instance token logprob confidence estimation
     - Inter-perspective divergence & confidence variance computation
     - Disagreement flag & HITL gateway escalation when divergence > threshold
  3. Aggregator Layer:
     - Synthesizes all perspectives, reconciles contradictions, and emits final consensus.
"""

from __future__ import annotations

import concurrent.futures
import json
import math
import os
import re
import time
import urllib.request
import urllib.error
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

try:
    from .agent_protocol import AgentMessage
    from .hitl_gateway import create_hitl_gateway, RiskLevel
    from .swarm_roles import get_swarm_role
except (ImportError, ValueError):
    from agent_protocol import AgentMessage
    from hitl_gateway import create_hitl_gateway, RiskLevel
    from swarm_roles import get_swarm_role


DEFAULT_LLAMA_SERVER_URL = os.getenv("LLAMA_SERVER_URL", "http://127.0.0.1:8138/v1")


@dataclass
class MoAResult:
    """Outcome of a complete Mixture-of-Agents deliberation cycle."""
    final_response: str
    proposals: Dict[str, AgentMessage]
    aggregator_message: AgentMessage
    confidence: float
    disagreement_variance: float
    disagreement_flag: bool
    escalated_to_hitl: bool
    duration_ms: float
    trace_id: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "final_response": self.final_response,
            "proposals": {k: v.to_dict() for k, v in self.proposals.items()},
            "aggregator_message": self.aggregator_message.to_dict(),
            "confidence": self.confidence,
            "disagreement_variance": self.disagreement_variance,
            "disagreement_flag": self.disagreement_flag,
            "escalated_to_hitl": self.escalated_to_hitl,
            "duration_ms": self.duration_ms,
            "trace_id": self.trace_id,
        }


def _call_llama_server(
    messages: List[Dict[str, str]],
    temperature: float = 0.2,
    top_p: float = 0.9,
    max_tokens: int = 1024,
    base_url: str = DEFAULT_LLAMA_SERVER_URL,
    timeout: float = 60.0,
) -> Tuple[str, float, Dict[str, Any]]:
    """
    Sends chat completion request to local llama-server, extracting content and logprob confidence.
    Returns: (content_text, confidence_score, metadata)
    """
    payload = {
        "messages": messages,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
        "logprobs": True,
        "top_logprobs": 1,
    }

    url = f"{base_url.rstrip("/")}/chat/completions"
    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data_bytes,
        headers={"Content-Type": "application/json", "Authorization": "Bearer local"},
        method="POST",
    )

    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            res_json = json.loads(body)
    except Exception as exc:
        duration_ms = (time.time() - t0) * 1000
        return f"[Execution Fallback: {exc}]", 0.50, {"error": str(exc), "duration_ms": duration_ms}

    duration_ms = (time.time() - t0) * 1000
    choice = res_json.get("choices", [{}])[0]
    content = choice.get("message", {}).get("content", "").strip()

    # Calculate confidence from logprobs
    logprobs_data = choice.get("logprobs", {}).get("content", [])
    token_logprobs: List[float] = []
    if isinstance(logprobs_data, list):
        for item in logprobs_data:
            lp = item.get("logprob")
            if lp is not None and isinstance(lp, (int, float)):
                token_logprobs.append(float(lp))

    if token_logprobs:
        mean_lp = sum(token_logprobs) / len(token_logprobs)
        confidence = float(math.exp(mean_lp))
        confidence = max(0.05, min(0.99, confidence))
    else:
        confidence = 0.85

    meta = {
        "duration_ms": duration_ms,
        "model": res_json.get("model", "gemma-4"),
        "prompt_tokens": res_json.get("usage", {}).get("prompt_tokens", 0),
        "completion_tokens": res_json.get("usage", {}).get("completion_tokens", 0),
        "tokens_scored": len(token_logprobs),
    }
    return content, confidence, meta


def compute_inter_perspective_divergence(texts: List[str]) -> float:
    """
    Computes lexical and semantic divergence across proposals using Jaccard distance over word tokens.
    Returns divergence score in [0.0, 1.0].
    """
    if len(texts) < 2:
        return 0.0

    def tokenize_words(t: str) -> set:
        words = re.findall(r"\b[a-zA-Z]{3,}\b", t.lower())
        return set(words)

    word_sets = [tokenize_words(t) for t in texts]
    distances = []
    for i in range(len(word_sets)):
        for j in range(i + 1, len(word_sets)):
            s1, s2 = word_sets[i], word_sets[j]
            if not s1 or not s2:
                distances.append(0.5)
                continue
            inter = len(s1.intersection(s2))
            union = len(s1.union(s2))
            jaccard = inter / union if union > 0 else 0.0
            distances.append(1.0 - jaccard)

    return sum(distances) / len(distances) if distances else 0.0


class MoAEngine:
    """
    Production Mixture-of-Agents Engine orchestrating 3 Proposers + 1 Aggregator.
    """

    def __init__(
        self,
        base_url: str = DEFAULT_LLAMA_SERVER_URL,
        disagreement_threshold: float = 0.45,
        hitl_mode: str = "yolo",
    ):
        self.base_url = base_url
        self.disagreement_threshold = disagreement_threshold
        self.hitl_gateway = create_hitl_gateway(mode=hitl_mode, auto_approve_low=True)

    def _generate_proposer(
        self,
        role: str,
        system_prompt: str,
        query: str,
        temperature: float,
        top_p: float,
        trace_id: str,
        context: Optional[str] = None,
    ) -> AgentMessage:
        user_content = query
        if context:
            user_content = f"""Context:
{context}

Task:
{query}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        content, confidence, meta = _call_llama_server(
            messages=messages,
            temperature=temperature,
            top_p=top_p,
            max_tokens=1536,
            base_url=self.base_url,
        )

        return AgentMessage(
            role=role,
            content=content,
            confidence=confidence,
            metadata=meta,
            trace_id=trace_id,
        )

    def run_moa(
        self,
        query: str,
        context: Optional[str] = None,
        timeout: float = 60.0,
    ) -> MoAResult:
        """Executes full MoA Proposer -> Scoring -> Escalation -> Aggregator cycle."""
        trace_id = f"moa-{uuid.uuid4().hex[:10]}"
        t0 = time.time()

        proposer_specs = [
            (
                "proposer_analytical",
                (
                    "You are a rigorous analytical reasoning expert in a Mixture-of-Agents collective. "
                    "Deconstruct the question with formal logic, step-by-step causality, mathematical/algorithmic "
                    "precision, and explicit empirical proofs. Deliver structured, deductive analysis."
                ),
                0.1,
                0.90,
            ),
            (
                "proposer_creative",
                (
                    "You are an innovative lateral strategist in a Mixture-of-Agents collective. "
                    "Explore unconventional hypotheses, novel architectures, non-obvious trade-offs, and creative "
                    "alternatives that purely deductive reasoning might overlook. Emphasize breadth and opportunity."
                ),
                0.7,
                0.95,
            ),
            (
                "proposer_critic",
                (
                    "You are an adversarial red-team security and correctness auditor in a Mixture-of-Agents collective. "
                    "Actively hunt for hidden assumptions, failure modes, boundary constraints, security vulnerabilities, "
                    "and logical fallacies. Scrutinize every proposal with aggressive skepticism."
                ),
                0.1,
                0.90,
            ),
        ]

        # 1. Proposer Layer: Run 3 instances in parallel
        proposals: Dict[str, AgentMessage] = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_map = {
                executor.submit(
                    self._generate_proposer,
                    role=role,
                    system_prompt=prompt,
                    query=query,
                    temperature=temp,
                    top_p=top_p,
                    trace_id=trace_id,
                    context=context,
                ): role
                for role, prompt, temp, top_p in proposer_specs
            }
            for fut in concurrent.futures.as_completed(future_map):
                role = future_map[fut]
                proposals[role] = fut.result()

        # 2. Consensus Scoring & Disagreement Analysis
        confidences = [msg.confidence for msg in proposals.values()]
        mean_conf = sum(confidences) / len(confidences)
        conf_variance = sum((c - mean_conf) ** 2 for c in confidences) / len(confidences)

        texts = [msg.content for msg in proposals.values()]
        lexical_divergence = compute_inter_perspective_divergence(texts)

        # Composite disagreement metric: 60% semantic/lexical distance + 40% confidence variance
        disagreement_score = (0.60 * lexical_divergence) + (0.40 * min(1.0, math.sqrt(conf_variance) * 3.0))
        disagreement_flag = disagreement_score > self.disagreement_threshold
        escalated_to_hitl = False

        if disagreement_flag:
            escalated_to_hitl = True
            self.hitl_gateway.request_checkpoint(
                action_id=f"checkpoint-{trace_id}",
                action_type="moa_disagreement_escalation",
                target="quorum_audit_consensus",
                summary=f"MoA Proposer divergence detected: score={disagreement_score:.2f} > {self.disagreement_threshold:.2f}",
                diff_or_payload=json.dumps(
                    {
                        "divergence": disagreement_score,
                        "confidences": {r: m.confidence for r, m in proposals.items()},
                        "summaries": {r: m.content[:150] for r, m in proposals.items()},
                    },
                    indent=2,
                ),
                metadata={"trace_id": trace_id, "disagreement_score": disagreement_score},
            )

        # 3. Aggregator Layer: Synthesis Prompt
        aggregator_system_prompt = """You are the authoritative Synthesizer in a Mixture-of-Agents (MoA) architecture.
You have received 3 distinct expert perspectives: Analytical Reasoner, Creative Strategist, and Red-Team Critic.
Your goal is to synthesize these perspectives into a unified, definitive consensus response:
1. Universal Agreement: State core points where all experts agree.
2. Conflict Resolution: Directly address tensions or criticisms raised by the Critic.
3. Authoritative Synthesis: Formulate the final definitive solution with balanced precision."""

        p_analytical = proposals.get("proposer_analytical")
        p_creative = proposals.get("proposer_creative")
        p_critic = proposals.get("proposer_critic")

        agg_prompt = f"""User Query: {query}

=== PERSPECTIVE 1: Analytical Reasoner (Confidence: {p_analytical.confidence if p_analytical else 0.8:.2f}) ===
{p_analytical.content if p_analytical else ""}

=== PERSPECTIVE 2: Creative Strategist (Confidence: {p_creative.confidence if p_creative else 0.8:.2f}) ===
{p_creative.content if p_creative else ""}

=== PERSPECTIVE 3: Red-Team Critic (Confidence: {p_critic.confidence if p_critic else 0.8:.2f}) ===
{p_critic.content if p_critic else ""}

Produce the synthesized consensus now:"""

        agg_messages = [
            {"role": "system", "content": aggregator_system_prompt},
            {"role": "user", "content": agg_prompt},
        ]

        agg_content, agg_conf, agg_meta = _call_llama_server(
            messages=agg_messages,
            temperature=0.4,
            top_p=0.90,
            max_tokens=2048,
            base_url=self.base_url,
        )

        agg_msg = AgentMessage(
            role="synthesizer",
            content=agg_content,
            confidence=agg_conf,
            metadata=agg_meta,
            trace_id=trace_id,
        )

        total_duration_ms = (time.time() - t0) * 1000

        return MoAResult(
            final_response=agg_content,
            proposals=proposals,
            aggregator_message=agg_msg,
            confidence=(mean_conf * 0.4) + (agg_conf * 0.6),
            disagreement_variance=conf_variance,
            disagreement_flag=disagreement_flag,
            escalated_to_hitl=escalated_to_hitl,
            duration_ms=total_duration_ms,
            trace_id=trace_id,
        )


_DEFAULT_MOA_ENGINE: Optional[MoAEngine] = None


def get_moa_engine(base_url: str = DEFAULT_LLAMA_SERVER_URL) -> MoAEngine:
    global _DEFAULT_MOA_ENGINE
    if _DEFAULT_MOA_ENGINE is None:
        _DEFAULT_MOA_ENGINE = MoAEngine(base_url=base_url)
    return _DEFAULT_MOA_ENGINE


def run_moa_debate(query: str, context: Optional[str] = None) -> MoAResult:
    """One-line high-level entrypoint to run MoA collective intelligence deliberation."""
    return get_moa_engine().run_moa(query=query, context=context)
