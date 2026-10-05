# Rollback Demonstration — Evening 5

**Scope:** Local demonstration only. Not a production rollback.

## Scenario

A harmless configuration change was made (temperature 0.2 → 0.9 in
`app/model.py`), the evaluation was re-run, and the change was reverted
to demonstrate that a known-good state can be restored and verified.

## Timeline

| Step | Command | Commit | Result |
|---|---|---|---|
| 1. Known-good state | `git rev-parse HEAD` | `<sha1>` | — |
| 2. Known-good eval | `EVAL_TAG=known_good ...` | — | <N>/20 |
| 3. Harmless change | edit temperature; `git commit` | `<sha2>` | — |
| 4. Eval after change | `EVAL_TAG=temp_0_9 ...` | — | <M>/20 |
| 5. Gate on bad state | `uv run python -m infra.release_gate` | — | <PASS/BLOCK> |
| 6. Rollback | `git revert HEAD --no-edit` | `<sha3>` | — |
| 7. Eval after rollback | `EVAL_TAG=after_rollback ...` | — | <N>/20 |

## What this proves

- The repository can be rolled back to a known-good state.
- The eval can verify that behaviour is restored.
- The rollback is recorded in git history as an auditable event.
- The release gate can block a regression before it ships
  (if the bad state failed the gate).

## What this does NOT prove

- Production rollback (requires coordinating app, model, prompt, data,
  and deployment state — git alone is insufficient).
- Zero-downtime rollback (would need blue-green or canary deployment).
- Side-effect rollback (no side effects exist — all write actions are mocked).

## Rollback manifest (for production use)

A real release must restore the full compatible set:

| Artifact | This project | Production requirement |
|---|---|---|
| App commit | `<git sha>` | Same |
| Container/image digest | n/a (local lab) | sha256 digest, signed |
| Runtime build | Ollama 0.32.9 | Pinned, recorded |
| Base-model revision | a80c4f17... | Immutable digest |
| Prompt version | hash of SYSTEM string | Version-controlled |
| Data / index version | `<git sha of data/>` | Same |
| Evaluation report | artifacts/eval_candidate.json | Same |

Rollback means restoring all of these together.