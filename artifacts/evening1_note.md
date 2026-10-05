# Evening 1 Handover — Data & Use Case

## Date
2026-10-05

## What was built
- Synthetic support-ticket dataset: 120 rows, 3 categories, 2 tenants
  - File: `data/tickets.parquet` (Parquet, ZSTD-compressed)
  - Schema: `ticket_id BIGINT, tenant_id BIGINT, label VARCHAR, body VARCHAR`
- Data tests: 6 passing (`tests/test_data.py`)
  - row count, unique IDs, required columns, permitted categories,
    tenant IDs, category balance
- Three runbooks with stable `source_id` + `tenant_id`
  - `data/runbook_access.md`      (rb-access-v1)
  - `data/runbook_billing.md`     (rb-billing-v1)
  - `data/runbook_reliability.md` (rb-reliability-v1)
- 20 evaluation questions (`eval/questions.jsonl`)
  - 17 answerable, 3 unanswerable (abstention tests)

## Measurable use case
Reduce time-to-draft for support replies. The copilot returns:
category + suggested reply + cited runbook source IDs.
**No write actions.** Refunds, deletions, account changes are out of scope
and remain mocked.

## Decisions made
- Used DuckDB (embedded, in-memory) to generate the dataset; exported to Parquet.
- Used `uv` for reproducible environment + lockfile.
- Kept all data synthetic — no real customer data touched.
- Attached `tenant_id` to every ticket and runbook so retrieval can filter
  by caller access (Evening 2 requirement).

## Unverified / open
- Databricks Delta-table ingestion — no workspace used.
  Planned table name: `dev_catalog.support.tickets`
  Owner: TBD
  Input: `data/tickets.parquet`
  Tests: same 6 as local
  Schedule: daily batch (not yet created)
  **Status: unverified — not executed.**
- Real tenant boundaries: synthetic only. Must be replaced with
  authorized data before any production discussion.

## Next evening (Evening 2)
- Serve one local model behind a loopback endpoint
- Add retrieval from the 3 runbooks
- Record baseline latency and a grounded-vs-ungrounded comparison