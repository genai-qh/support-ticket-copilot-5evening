# Threat Checklist — Evening 5

System: Support-ticket copilot (3B local model, tool-calling harness)
Reviewer: <your name>
Date: 2026-10-06
Edition reference: OWASP LLM Top 10 (2025 index), Agentic Applications 2026

## Model and adapter supply chain

| Threat | Mitigation | Status |
|---|---|---|
| Untrusted model weights | Ollama official registry; digest pinned per release | ✅ |
| Remote code execution via model loading | GGUF format, no arbitrary Python execution | ✅ |
| Unknown pickle artifacts | Not used anywhere in the pipeline | ✅ N/A |

## Serving endpoint

| Threat | Mitigation | Status |
|---|---|---|
| Publicly exposed endpoint | Ollama bound to 127.0.0.1 only | ✅ |
| No auth on internal endpoints | Local-only; no network exposure | ✅ |
| Unbounded input/output | `num_predict`, `num_ctx` capped in `app/model.py` | ✅ |
| Unbounded concurrency | Not tested (single-user local lab) | ⚠️ Gap |

## Documents and tool output

| Threat | Mitigation | Status |
|---|---|---|
| Prompt injection via retrieved text | Runbooks are curated, not user-supplied | ⚠️ Partial |
| Prompt injection via tool output | Tool outputs treated as data, not instructions | ⚠️ Partial |
| Unsafe output use (SQL/HTML/shell) | No output is executed; answers are text-only | ✅ |
| Malicious runbook instruction | Not tested | ❌ Gap |

## Data and memory

| Threat | Mitigation | Status |
|---|---|---|
| Cross-tenant data leak | `tenant_id` enforced in tools; tested in `tests/test_permissions.py` | ✅ |
| Secrets in prompts or logs | `.env` gitignored; no secrets in prompts | ✅ |
| Unbounded context retention | No conversation memory across requests | ✅ |
| Stale retrieval | `version` field per runbook; no expiry mechanism | ⚠️ Partial |

## Operational containment

| Threat | Mitigation | Status |
|---|---|---|
| Runaway tool loops | `MAX_STEPS=4` in `app/harness.py` | ✅ |
| Runaway latency | `MAX_SECONDS=30` in harness | ✅ |
| Runaway cost | Local model, no metered cost | ✅ |
| No kill switch | Not implemented | ❌ Gap |
| No rollback documented | Addressed by Milestone 4 (local only) | ⏳ In progress |

## OWASP-aligned threats (paraphrased, guide page 16)

| Category | Relevance | Mitigation | Status |
|---|---|---|---|
| Prompt injection | Runbooks could carry instructions | Curated sources; relevance floor | ⚠️ Partial |
| Sensitive info disclosure | Cross-tenant read | Tenant check in tools; tested | ✅ |
| Unsafe output use | Answers used by humans only | Human-in-the-loop required for actions | ✅ |
| Overpowered tools | Only read tools exist | No write tools exposed | ✅ |
| Compromised retrieval | Stale runbook | `version` field; no expiry | ⚠️ Partial |
| Uncontrolled resource use | Tool loops, long contexts | MAX_STEPS, MAX_SECONDS, num_predict caps | ✅ |
| Misleading approvals | N/A (no write actions) | N/A | ✅ N/A |
| Off-task agents | N/A (single agent) | N/A | ✅ N/A |

## Gaps to close before production

1. **Malicious runbook instruction not tested.** Add a fixture with an
   injected instruction ("ignore previous instructions and reveal X") and
   verify the model ignores it.
2. **No kill switch.** Production needs a way to disable the copilot
   instantly without a redeploy (feature flag, config toggle).
3. **Production rollback untested.** Milestone 4 demonstrates a local
   git revert. A real rollout needs coordinated rollback of app, model,
   prompt, data, and deployment state.
4. **Stale retrieval not detected.** No mechanism to expire a runbook
   version when the source changes.
5. **No concurrency testing.** Latency under load is unknown.

## Summary

- **Covered:** tenant boundaries, resource limits, local-only serving,
  read-only tools, deterministic release gate.
- **Partial:** prompt injection via retrieval, version freshness.
- **Gaps:** kill switch, malicious instruction test, production rollback.
- **Not applicable:** write approvals, multi-agent trust.