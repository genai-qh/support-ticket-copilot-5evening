# A2A Task Contract — Ticket Triage Specialist

## Purpose
Delegate ticket triage to a specialist agent. Design only; not implemented.

## Input
- ticket_id: integer
- allowed_source_ids: list[str]
- deadline_seconds: integer
- max_cost_usd: number

## Output
- ticket_id: integer
- category: string
- summary: string
- citations: list[str]
- confidence: number

## States
submitted → working → completed
                    → failed
                    → cancelled
                    → input-required

## Security
- allowed_source_ids is a hard allowlist
- Deadline and cost enforced by caller, not the agent
- No write actions; report only

## Notes
Human labels shown here. Wire format uses A2A v1.0 enums.
Not implemented; MCP tools are used directly instead.