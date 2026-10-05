## Release gate — final state

| Check | Result |
|---|---|
| Data and schema tests | ✓ PASS (6/6) |
| Environment sanity | ✓ PASS |
| Tool imports | ✓ PASS |
| Evaluation | ✓ PASS |
| Unanswerable questions | 3/3 |
| Total score | 16/20 |
| Avg latency | 0.633s |

**Gate outcome: RELEASE ALLOWED.**

## Key finding — deterministic safety net

The relevance floor (`MIN_RELEVANCE = 2`, stop-word filtered) moved
the abstention decision from the model to code. Effects:

- Unanswerable questions now abstain 3/3, deterministically.
- Average latency dropped from ~1.3s to ~0.63s because weak-evidence
  questions skip the model call entirely.
- The fix does not depend on prompt compliance — it's an enforceable
  control around an unreliable component.