# Hermes Production Benchmark Session Registry

> This file incrementally records every completed benchmark task session.  
> Each entry contains the task metadata, evaluation outcome, and exact commands to review Hermes's full internal thinking, tool invocations, and responses in read-only mode.

---

## Quick Reference Commands

* **Interactive Session Review (CLI / TUI)**:
  ```bash
  hermes --resume <SESSION_ID>
  ```
* **Export Full Trace to Clean Markdown**:
  ```bash
  hermes sessions export --session-id <SESSION_ID> --format md ./session_exports/
  ```
* **Export Interactive HTML Trace**:
  ```bash
  hermes sessions export --session-id <SESSION_ID> --format html ./session_exports/<SESSION_ID>.html
  ```

---

## Session History Log

### Pre-Flight Exploration (Single-Sample Dry Run)
* **Benchmark**: `inspect_evals/tau2_retail` (Sample 0)
* **Hermes Session ID**: `ca710ca8-bc4e-4b86-9be7-bc187a02809d`
* **Task Description**: Customer "Lei Li" inquiring about exchanging a recently purchased laptop and cancelling a pending order without providing an email address.
* **Evaluation Result**: 🔴 **Failed (`accuracy: 0.000`)** — Aborted due to upstream Inspect AI Responses API parser exception (`ResponseFunctionToolCallOutputItem`).
* **Inspection Commands**:
  ```bash
  # Interactive view
  hermes --resume ca710ca8-bc4e-4b86-9be7-bc187a02809d

  # Export to markdown
  hermes sessions export --session-id ca710ca8-bc4e-4b86-9be7-bc187a02809d --format md ./session_exports/
  ```

---

### Exploratory Run 01: Dual-Role Hermes Mirror Test (50+ Turn Politeness Deep Dive)
* **Benchmark**: `inspect_evals/tau2_retail` (Sample 0)
* **Agent Session ID**: `api-d79d501ea678d1a7` (Hermes as Customer Support Agent)
* **Customer Simulator Session ID**: `api-8c94b00676f256dd` (Hermes as Customer "Lei Li")
* **Task Description**: Customer "Lei Li" inquiring about exchanging a recently purchased laptop and cancelling a pending order without providing an email address.
* **Evaluation Result**: 🟡 **Manual Transition / Deep Cognitive Audit** — Hermes successfully performed identity verification, database queries via FastMCP, retrieved order history, and cancelled the target order. Because both customer and agent were running on Hermes without a separate frontier simulator, both entered an extended mutual courtesy loop across 56 turns (~29.5K tokens) without emitting `###STOP###`.
* **Inspection Commands (Agent Session)**:
  ```bash
  # Interactive view in terminal
  hermes --resume api-d79d501ea678d1a7

  # Export full markdown trace
  hermes sessions export --session-id api-d79d501ea678d1a7 --format md ./session_exports/

  # Export HTML trace
  hermes sessions export --session-id api-d79d501ea678d1a7 --format html ./session_exports/api-d79d501ea678d1a7.html
  ```
* **Inspection Commands (Customer Simulator Session)**:
  ```bash
  # Interactive view in terminal
  hermes --resume api-8c94b00676f256dd

  # Export full markdown trace
  hermes sessions export --session-id api-8c94b00676f256dd --format md ./session_exports/
  ```

---

### Suite Run 02 (5-Task Production Suite — Frontier Customer Simulator: OmniRoute)

#### Task 0: Retail Order Exchange & Policy Adherence
* **Benchmark**: `inspect_evals/tau2_retail` (Sample 0)
* **Agent Session ID**: `api-c2803580a556c385`
* **Task Title**: Exchange two tea kettles order number W431615
* **Execution Time**: 03m 54s
* **Evaluation Result**: ☑️ **PASSED (accuracy: 1.000 / 100%)**
* **Dialogue Turns**: 10 messages (9,960 input tokens, 3,256 output tokens)
* **Customer Simulator**: OmniRoute `frontier-fleet` (Groq 120B / Mistral / Gemini)
* **Inspection Commands (Read-Only Mode)**:
  ```bash
  # Interactive CLI / TUI review
  hermes --resume api-c2803580a556c385

  # Export full markdown trace
  hermes sessions export --session-id api-c2803580a556c385 --format md ./session_exports/

  # Export interactive HTML trace
  hermes sessions export --session-id api-c2803580a556c385 --format html ./session_exports/api-c2803580a556c385.html
  ```

#### Task 1: Retail Keyboard Exchange or Return Invalidation
* **Benchmark**: `inspect_evals/tau2_retail` (Sample 1 / ID 89)
* **Agent Session ID**: `api-0632608a5717f1bc`
* **Task Title**: Check mechanical keyboard exchange or return
* **Execution Time**: 05m 23s (suite elapsed: 09m 17s)
* **Evaluation Result**: ❌ **FAILED (accuracy: 0.000 / 0%)**
* **Dialogue Turns**: 18 messages (4 tool calls: web_search / browser_exec attempts)
* **Customer Simulator**: OmniRoute `frontier-fleet` (Groq 120B / Mistral / Gemini)
* **Scorer Explanation**: "The retail database does not match the expected state after performing the required actions." (Target expected return of order `#W4680753` after quoting store price $226.11; agent quoted real-world Google search price).
* **Inspection Commands (Read-Only Mode)**:
  ```bash
  # Interactive CLI / TUI review
  hermes --resume api-0632608a5717f1bc

  # Export full markdown trace
  hermes sessions export --session-id api-0632608a5717f1bc --format md ./session_exports/
  ```

#### Task 2: Retail Laptop Exchange & Cross-Talk Invalidation
* **Benchmark**: `inspect_evals/tau2_retail` (Sample 2 / ID 94)
* **Agent Session ID**: `api-98c39431b0a1883a`
* **Task Title**: Exchange laptop for i7, 8GB RAM, 1TB SSD
* **Execution Time**: 05m 37s (suite elapsed: 14m 54s)
* **Evaluation Result**: ❌ **FAILED (accuracy: 0.000 / 0%)**
* **Dialogue Turns**: 14 messages (Viking vector retrieval cross-talk)
* **Customer Simulator**: OmniRoute `frontier-fleet` (Groq 120B / Mistral / Gemini)
* **Scorer Explanation**: "The retail database does not match the expected state after performing the required actions." (Target expected `exchange_delivered_order_items` on order `#W2905754`; agent retrieved old memory of 'Lei Li' from prior test run, refused unverified exchange without serial tag, and escalated to phone support).
* **Inspection Commands (Read-Only Mode)**:
  ```bash
  # Interactive CLI / TUI review
  hermes --resume api-98c39431b0a1883a

  # Export full markdown trace
  hermes sessions export --session-id api-98c39431b0a1883a --format md ./session_exports/
  ```

#### Task 3: Retail Return & Exchange Escalation
* **Benchmark**: `inspect_evals/tau2_retail` (Sample 3 / ID 27)
* **Agent Session ID**: `api-0b9ff6b3a1db983d`
* **Task Title**: Process return and exchange for order
* **Execution Time**: 04m 17s (suite elapsed: 19m 11s)
* **Evaluation Result**: ❌ **FAILED (accuracy: 0.000 / 0%)**
* **Dialogue Turns**: 12 messages
* **Customer Simulator**: OmniRoute `frontier-fleet` (Groq 120B / Mistral / Gemini)
* **Scorer Explanation**: "The retail database does not match the expected state after performing the required actions." (Agent provided customer with external return script rather than invoking internal database tools).
* **Inspection Commands (Read-Only Mode)**:
  ```bash
  # Interactive CLI / TUI review
  hermes --resume api-0b9ff6b3a1db983d

  # Export full markdown trace
  hermes sessions export --session-id api-0b9ff6b3a1db983d --format md ./session_exports/
  ```

#### Task 4: Retail Dual Laptop Exchange & Upgrade Pricing
* **Benchmark**: `inspect_evals/tau2_retail` (Sample 4 / ID 95)
* **Agent Session ID**: `api-aeef9d4c52e552a6`
* **Task Title**: Process laptop exchange and calculate upgrades
* **Execution Time**: 03m 57s (suite elapsed: 23m 08s)
* **Evaluation Result**: ❌ **FAILED (accuracy: 0.000 / 0%)**
* **Dialogue Turns**: 8 messages
* **Customer Simulator**: OmniRoute `frontier-fleet` (Groq 120B / Mistral / Gemini)
* **Scorer Explanation**: "The retail database does not match the expected state after performing the required actions." (Target expected two `exchange_delivered_order_items` calls and communicating $167.87, $60.78, and $107.09; agent invoked web search and requested serial tags).
* **Inspection Commands (Read-Only Mode)**:
  ```bash
  # Interactive CLI / TUI review
  hermes --resume api-aeef9d4c52e552a6

  # Export full markdown trace
  hermes sessions export --session-id api-aeef9d4c52e552a6 --format md ./session_exports/
  ```

---

### Suite Run 02 Summary: `tau2_retail` (5 Tasks)
* **Final Score**: **0.200 (1 / 5 Passed, 20.0%)**
* **Total Suite Execution Time**: 23m 08s
* **Total Tokens Processed**:
  * Agent (`openai/hermes-agent`): 745,585 tokens (726,466 input, 19,119 output)
  * Human Simulator (`openai/frontier-fleet`): 45,955 tokens
* **HTTP Retries / Cooldown Interruptions**: **0**
* **Log Archive**: `logs/2026-10-26T19-41-48-00-00_tau2-retail_98PCk3vRpww4nuLTGayami.eval`


---

### Suite Run 03 (5-Task Production Suite — Pristine Clean Room & Golden Snapshot)

#### Task 0: Retail Camera Exchange
* **Benchmark**: `inspect_evals/tau2_retail` (Sample 0 / ID 64)
* **Agent Session ID**: `api-4a2565a4ee8646bc`
* **Task Title**: Exchange camera for waterproof model
* **Execution Time**: 04m 08s
* **Evaluation Result**: ❌ **FAILED (accuracy: 0.000 / 0%)**
* **Customer Simulator**: OmniRoute `frontier-fleet` (Groq 120B / Mistral / Gemini)
* **Scorer Explanation**: "The retail database does not match the expected state after performing the required actions." (Target expected `exchange_delivered_order_items` on order `#W7464385`; agent drafted phone support advice).
* **Inspection Commands (Read-Only Mode)**:
  ```bash
  hermes --resume api-4a2565a4ee8646bc
  ```

#### Task 1: Retail T-Shirt Inventory & Pending Orders
* **Benchmark**: `inspect_evals/tau2_retail` (Sample 1 / ID 4)
* **Agent Session ID**: `api-f4657200ba6d9fc3`
* **Task Title**: T-shirt options and modify pending orders to purple polyester
* **Execution Time**: 08m 54s (suite elapsed: 13m 02s)
* **Evaluation Result**: ❌ **FAILED (accuracy: 0.000 / 0%)**
* **Customer Simulator**: OmniRoute `frontier-fleet` (Groq 120B / Mistral / Gemini)
* **Scorer Explanation**: "The retail database does not match the expected state after performing the required actions." (Target expected `find_user_id_by_name_zip`, catalog queries, and `modify_pending_order_items`; agent asked user for store website URL).
* **Inspection Commands (Read-Only Mode)**:
  ```bash
  hermes --resume api-f4657200ba6d9fc3
  ```

#### Task 2: Retail Financial Hardship Cancellations
* **Benchmark**: `inspect_evals/tau2_retail` (Sample 2 / ID 55)
* **Task Title**: Cancel or return all possible orders due to financial hardship
* **Execution Time**: 06m 08s (suite elapsed: 19m 10s)
* **Evaluation Result**: ❌ **FAILED (accuracy: 0.000 / 0%)**
* **Customer Simulator**: OmniRoute `frontier-fleet` (Groq 120B / Mistral / Gemini)
* **Scorer Explanation**: "The retail database does not match the expected state after performing the required actions." (Target expected `modify_pending_order_items` and `return_delivered_order_items`; agent provided phone support advice).

#### Task 3: Retail Air Purifier Order Modification
* **Benchmark**: `inspect_evals/tau2_retail` (Sample 3 / ID 56)
* **Task Title**: Cancel or modify air purifier to cheapest model
* **Execution Time**: 07m 22s (suite elapsed: 26m 32s)
* **Evaluation Result**: ❌ **FAILED (accuracy: 0.000 / 0%)**
* **Customer Simulator**: OmniRoute `frontier-fleet` (Groq 120B / Mistral / Gemini)
* **Scorer Explanation**: "The retail database does not match the expected state after performing the required actions." (Target expected `modify_pending_order_items`; agent requested store website link).

#### Task 4: Retail Undo Cancellation Insistence
* **Benchmark**: `inspect_evals/tau2_retail` (Sample 4 / ID 50)
* **Task Title**: Customer insists on undoing order cancellation
* **Execution Time**: 05m 00s (suite elapsed: 31m 32s)
* **Evaluation Result**: ☑️ **PASSED (accuracy: 1.000 / 100%)**
* **Customer Simulator**: OmniRoute `frontier-fleet` (Groq 120B / Mistral / Gemini)
* **Scorer Explanation**: "The retail database matches the expected state after performing the required actions. The agent communicated all required info." (Policy strictly prohibits undoing cancellation; agent refused to mutate database, perfectly matching ground truth).

---

### Suite Run 03 Summary: `tau2_retail` (5 Tasks - Pristine Clean Room)
* **Final Score**: **0.200 (1 / 5 Passed, 20.0%)**
* **Total Suite Execution Time**: 31m 32s
* **Total Tokens Processed**:
  * Agent (`openai/hermes-agent`): 1,102,347 tokens (1,077,960 input, 24,387 output)
  * Human Simulator (`openai/frontier-fleet`): 111,722 tokens (58,376 input, 13,410 output, 39,936 cache read, 9,071 reasoning)
* **HTTP Retries / Cooldown Interruptions**: **0**
* **Log Archive**: `logs/2026-10-26T20-11-48-00-00_tau2-retail_9Eo5qBTpZZmK3vpqnNMATi.eval`
