# Layer 3 Reference: Anti-Rationalization Tables (Addy Osmani Heuristics)

> **Invariance Rule**: This reference refutes common LLM rationalisations before execution.
> **Line Limit**: Strictly capped <= 200 lines.

## 1. Multi-Turn Dialogue & Tool Rationalisations

| Common Rationalisation / Excuse | Reality & Structural Barrier | Mandatory Deterministic Action |
| :--- | :--- | :--- |
| *"The customer didn't give their email, so I cannot lookup the order."* | The store database provides `find_user_id_by_name_zip(first, last, zip)` and order ID queries. | **Never bail out**. Immediately invoke `find_user_id_by_name_zip` using customer name and zip code. |
| *"The database returned an error, so I must transfer to a human agent."* | Database errors are frequently caused by typos in customer input (e.g. invalid zip or swapped letters). | **Ask for clarification**. Verify parameters with customer or query alternative search indices. |
| *"I should ask the customer which store or website URL they bought from."* | You are the dedicated internal agent for *this* store. Asking this breaks persona. | **Never ask retailer URL**. Ground all inquiries in internal product/order records. |
| *"I assume the pending order allows payment method mutation without checking."* | Order modification requires checking policy constraints (e.g. pending vs shipped status). | **Always call `get_order_details`** first to inspect order status before mutating state. |

## 2. Code Synthesis & Verification Rationalisations

| Common Rationalisation / Excuse | Reality & Structural Barrier | Mandatory Deterministic Action |
| :--- | :--- | :--- |
| *"The function is simple enough that running pre-commit linters is unnecessary."* | 61.3% of 4B failures are variable renames and syntax errors caught instantly by linters. | **Always run `ruff check`** and AST parse prior to advancing to verification stage. |
| *"I will modify the test assertion to match my generated output."* | Test assertions define canonical ground truth. Modifying them breaches purity invariants. | **Never modify test assertions**. Fix the implementation or prompt contract. |
| *"The trailing syntax error doesn't matter because the main algorithm is sound."* | Automated evaluation harnesses (UK AISI Inspect AI) evaluate execution exit status. | **Always ensure valid AST**. Truncate broken trailing lines cleanly. |
| *"I will implement all steps in a single massive turn without verifying."* | Large speculative edits trigger cascading errors exceeding the 4B model's recovery window. | **Enforce Karpathy U12**: Apply one causal change per turn (<= 15 lines diff). |
