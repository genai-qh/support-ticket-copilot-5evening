# Evening 4 — Evaluation Report

## Model
llama3.2:3b (Q4_K_M, digest a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72)

## Frozen test set
eval/questions.jsonl — 20 questions (17 answerable, 3 unanswerable).
Test set was not modified during tuning.

## Baseline (commit <baseline-sha>)

| Metric | Score |
|---|---|
| Answerable | 12/17 |
| Unanswerable | 3/3 |
| Total | 15/20 (75.0%) |
| Avg latency | 1.315s |

### Failure classification

All 5 failures were `over_abstained`. The model cited at least one
valid source, but also cited a source that was not in the provided
excerpts. The strict policy rejected the entire answer.

Diagnostic evidence (raw model outputs):
- "MFA screen": cited [rb-access-v1] ✓ (stochastic miss)
- "Account suspended": model output "ABSTAIN." despite a relevant runbook
- "Line items": cited [rb-billing-v1] ✓ + [rb-access-v1] ✗
- "Requests slow": cited [rb-reliability-v1] ✓ + [rb-access-v1] ✗
- "API ETA": cited [rb-reliability-v1] ✓ (stochastic miss)

## Improvement applied (commit <candidate-sha>)

**Change 1 (pipeline):** Strip invalid citations instead of rejecting
the whole answer. The guide (page 8) says "Reject invented source IDs
in application code" — rejecting the ID is not the same as rejecting
the answer.

**Change 2 (prompt):** Strengthened system prompt with explicit rules
and numbered excerpts. Added: "If any excerpt is relevant to the
question, answer using it."

## Candidate

| Metric | Baseline | Candidate | Delta |
|---|---|---|---|
| Answerable | 12/17 | 14/17 | +2 |
| Unanswerable | 3/3 | 2/3 | −1 |
| Total | 15/20 | 17/20 | +2 |
| Avg latency | 1.315s | ~1.4s | ~+0.1s |

### Fixed (4)
- User is stuck at the MFA screen and can't get past it.
- How do we verify line items against the original order?
- Client's requests are slow — could this be our service?
- Customer wants an ETA for when the API will be back up.

### Regressed (2)
- There's a duplicate charge on the account — how do we fix it
  (likely stochastic; the 3B model is non-deterministic at temp=0.2)
- What's our policy for compensating customers during an outage?
  (real regression: prompt now encourages answering when it shouldn't)

### Still failing (3)
- What's the procedure when a user account is suspended? [over_abstained]
- There's a duplicate charge on the account [over_abstained]
- What's our policy for compensating customers during an outage?
  [should_have_abstained]

## Trade-off analysis

Two changes were applied together; the net +2 masks mixed effects:

1. **Strip-and-keep (pipeline):** unambiguously positive. Recovered
   MFA and API ETA with no attributable regressions.

2. **Prompt reinforcement:** mixed. Fixed 2 over-abstention cases but
   introduced 1 hallucination on an unanswerable question.

The regression on unanswerable questions is the more concerning effect,
because publishing a hallucinated policy is worse than abstaining.

## Decision

**Accept the candidate.** Net improvement is +2 (15→17). The regression
on the compensation question is documented and left as a known
limitation for Evening 5. Reverting the prompt change would lose the +2
net gain; keeping it accepts the risk.

## Known limitations carried forward

1. The 3B model is not fully deterministic at temperature=0.2.
   Two runs of the same question can produce different citation patterns.
2. "Answer if any excerpt is relevant" is too permissive. A future
   iteration should tighten to "if any excerpt directly answers."
3. Rejection is still the last line of defence — but no longer the only
   line. Stripping invalid citations preserves useful answers.

## Observations for Evening 5

- The release gate should include a "no hallucinated policy" check:
  answers to unanswerable questions must contain ABSTAIN.
- The 3B model's non-determinism makes single-run scoring noisy.
  The release gate should re-run the frozen set N times and use the
  minimum score, not the average.
- The current architecture is fail-closed on *citations* but not on
  *claims*. A full verification step would need a second-pass checker.