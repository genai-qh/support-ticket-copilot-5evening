# Evening 3 Handover — Tools & Harness

## What was built
- `app/tools.py`
  - `get_ticket(ticket_id, tenant_id)` — tenant-scoped, structured errors
  - `search_runbooks(query, tenant_id, k)` — bounded, tenant-scoped
- `app/harness.py`
  - Bounded loop: MAX_STEPS=4, MAX_SECONDS=30, MAX_OUTPUT_CHARS=4000
  - Two tools exposed to the model: get_ticket, search_runbooks
  - `tenant_id` is set by the caller, never by the model
  - Trace records each tool call: step, tool, args, result_keys
- `artifacts/a2a_contract.md`
  - Input: ticket_id, allowed_source_ids, deadline, cost cap, schema
  - States: submitted, working, completed, failed, input-required, cancelled

## Verified behavior
- Model called `get_ticket` for ticket questions
- Model called `search_runbooks` for runbook questions
- Cross-tenant access returned `{"error": "denied"}`
- Malformed inputs returned `{"error": "invalid_argument"}`
- Harness respected MAX_STEPS and MAX_SECONDS
- No credentials or tenant_id appeared in model-visible context

## Observed limitations (Evening 4 candidates)
1. **Small model misuses tools.** `llama3.2:3b` called `search_runbooks`
   for an out-of-scope "restaurant near office" question, then hallucinated
   generic advice instead of abstaining.
2. **No citations.** Unlike `app/grounded.py`, the harness doesn't force
   `[rb-xxx]` citations, so the model paraphrases freely.
3. **get_ticket returns tenant_id.** Consider stripping it to minimize
   model-visible metadata (page 16: "minimise retained context").

## Not done (deliberately)
- MCP server wrapping (Path 2, deferred)
- Real A2A execution (design contract only)
- HTTP/OAuth deployment (out of scope for this evening)

## Next evening (Evening 4)
- Evaluate against the 20 frozen questions
- Compare 3B vs 8B as baseline vs candidate
- Write a tuning recipe