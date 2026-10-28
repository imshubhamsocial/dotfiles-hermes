# Phase 39 Specification: Harness Responses API Rectification & Dual-Track Routing

* **ICM Layer**: Infrastructure (60% Allocation Tier)  
* **Context Budget**: < 2,048 tokens (Sub-8K Compliant)  
* **Input State**: GDR24 empirical failure logs (ValueError: Unexpected output type: ResponseFunctionToolCallOutputItem in openai_responses.py).  
* **Process**:  
  1. Mandate `-M responses_api=false` across all UK AISI Inspect AI CLI invocations to force standard `/v1/chat/completions` deserialization.  
  2. Separate Track A1 (Direct Model Function-Calling on Port 8138), Track A2 (Bridged Agentic OS on Port 1934 -> 8642), and Track B (ARC Challenge on Port 8642).  
* **Output Artifact**: `/var/home/imshubhamsocial/Desktop/GDR/GDR24/run_remediated_gauntlet.sh`.  
* **Tabu Rule**: Strike 2 rollback via `git checkout -- .`.
