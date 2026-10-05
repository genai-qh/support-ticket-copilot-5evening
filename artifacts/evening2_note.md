# Evening 2 — Baseline Model Call

## Configuration
- MODEL (.env): llama3.2:3b
- Runtime: Ollama (app)
- Endpoint: http://127.0.0.1:11434/api/chat
- Options: temperature=0.2, num_ctx=4096
- Model digest: a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72
- Quantization: Q4_K_M

## Baseline call
Prompt: "Classify this ticket: Cannot sign in. Return only access, billing, or reliability."
- Answer: <model ignored the format instruction; produced a paragraph>
- End-to-end latency: 0.910s

## Grounded comparison
| Question | Result |
|---|---|
| Cannot log in after reset | (rerun after fix) |
| Verify line items on invoice | cites rb-billing-v1 |
| Refund policy for annual plans | ABSTAIN (correct — unanswerable) |
| Restaurant recommendation | ABSTAIN (correct — unanswerable) |

## Observations
- 3B model ignores strict output-format instructions — note for Evening 4.
- Keyword retrieval returns overlapping hits (rb-access-v1 + rb-billing-v1 for a sign-in question) — note for Evening 4.
- Grounded answers add citations; ungrounded will hallucinate. (Verify with compare.py next.)

## Second model available
- llama3.1:latest (8.0B, Q4_K_M) — for candidate comparison in Evening 4