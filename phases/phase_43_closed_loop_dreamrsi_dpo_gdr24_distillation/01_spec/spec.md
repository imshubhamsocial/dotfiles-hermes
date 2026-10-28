# Phase 43 Specification: Closed-Loop dreamRSI DPO Preference Compilation & Hardware Isolation

* **ICM Layer**: AI Cognition (10% Allocation Tier)  
* **Context Budget**: < 3,000 tokens (Sub-8K Compliant)  
* **Input State**: GDR24 empirical diagnostic transcripts (ARC Challenge successes, Tau-bench tool omissions, role disclaimers).  
* **Process**:  
  1. Deploy `dream_rsi_workspace/compile_gdr24_dpo_pairs.py` to compile structural preference triples `(prompt, chosen, rejected)` across 3 archetypes:
     - Archetype 1: `secondary_key_lookup_precedence` (chosen: invoke `find_user_id_by_name_zip` and `get_order_details`; rejected: role disclaimer / web search).
     - Archetype 2: `epistemic_negative_policy_verification` (chosen: inspect DB records before policy-grounded refusal; rejected: AI assistant disclaimer).
     - Archetype 3: `crystallized_deductive_classification_verification` (chosen: scientific deduction based on structural invariants; rejected: distractor).
  2. Enforce strict de-identification filtering with zero benchmark literals (`tau2`, `arc_challenge`, customer PII, order IDs).  
  3. Enforce CPU-only offload invariant (`CUDA_VISIBLE_DEVICES=""`).  
* **Output Artifact**: `dream_rsi_workspace/lora_atropos_dpo.jsonl`.
