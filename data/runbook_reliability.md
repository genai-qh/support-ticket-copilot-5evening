---
source_id: rb-reliability-v1
tenant_id: 1
version: 1
---

# API Reliability Runbook

## API request timed out
1. Check the service status dashboard for the affected region.
2. Verify the client's request timeout and retry configuration.
3. If the service is degraded, provide the incident link and estimated resolution window.
4. Do not promise a specific fix time without an incident confirmation.

## Known outage
1. Confirm the outage on the status dashboard before replying.
2. Provide the affected regions and the incident ID.
3. Set expectations using the published ETA; do not invent one.

## Slow requests
1. Ask the customer for a request ID and approximate timestamp.
2. Check server-side latency metrics for the affected endpoint.
3. If latency is above baseline, escalate to the reliability on-call.

## Client-side timeout configuration
1. Confirm the customer's client uses exponential backoff with jitter.
2. Recommended minimum timeout: 30 seconds for non-interactive requests.
3. Do not advise disabling retries to "fix" intermittent errors.