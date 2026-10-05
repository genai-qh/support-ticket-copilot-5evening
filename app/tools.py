# app/tools.py
import json
from pathlib import Path
import duckdb

from app.retrieval import search as _search_runbooks

TICKETS_PARQUET = "data/tickets.parquet"


def get_ticket(ticket_id: int, tenant_id: int) -> dict:
    """Fetch a ticket by ID, scoped to the caller's tenant.

    Returns a structured result. Never raises on 'not found' — returns
    {"error": "not_found"} instead, so the model can reason about it.
    """
    if not isinstance(ticket_id, int):
        return {"error": "invalid_argument", "detail": "ticket_id must be an integer"}

    with duckdb.connect() as db:
        row = db.execute(
            f"""
            SELECT ticket_id, tenant_id, label, body
            FROM '{TICKETS_PARQUET}'
            WHERE ticket_id = ?
            """,
            [ticket_id],
        ).fetchone()

    if row is None:
        return {"error": "not_found", "ticket_id": ticket_id}

    found_tenant = row[1]
    if found_tenant != tenant_id:
        # Tenant boundary violated. Do NOT return the record.
        return {"error": "denied", "ticket_id": ticket_id}

    return {
        "ticket_id": row[0],
        "tenant_id": row[1],
        "category": row[2],
        "body": row[3],
    }

def search_runbooks(query: str, tenant_id: int, k: int = 2) -> dict:
    """Search runbooks for a query, scoped to the caller's tenant.

    Returns a bounded, structured result. Never returns raw file content
    outside the caller's permitted corpus.
    """
    if not isinstance(query, str):
        return {"error": "invalid_argument", "detail": "query must be a string"}

    query = query.strip()
    if len(query) == 0:
        return {"error": "invalid_argument", "detail": "query must be non-empty"}
    if len(query) > 500:
        return {"error": "invalid_argument", "detail": "query too long (max 500)"}

    k = max(1, min(k, 5))  # bound the result count

    hits = _search_runbooks(query, tenant_id=tenant_id, k=k)

    return {
        "query": query,
        "count": len(hits),
        "results": [
            {
                "source_id": h["source_id"],
                "version": h["version"],
                "excerpt": h["body"][:400],  # bounded excerpt
            }
            for h in hits
        ],
    }

if __name__ == "__main__":
    print("--- valid tenant ---")
    print(json.dumps(get_ticket(42, tenant_id=1), indent=2))

    print("\n--- authenticated but wrong tenant ---")
    print(json.dumps(get_ticket(42, tenant_id=2), indent=2))

    print("\n--- cross-tenant attempt ---")
    print(json.dumps(get_ticket(42, tenant_id=999), indent=2))

    print("\n--- not found ---")
    print(json.dumps(get_ticket(99999, tenant_id=1), indent=2))

    print("\n--- malformed ---")
    print(json.dumps(get_ticket("42", tenant_id=1), indent=2))

    print("\n--- authenticated but wrong tenant ---")
    print(json.dumps(get_ticket(42, tenant_id=2), indent=2))

    print("\n--- search_runbooks: valid ---")
    print(json.dumps(search_runbooks("cannot sign in", tenant_id=1), indent=2))

    print("\n--- search_runbooks: cross-tenant ---")
    print(json.dumps(search_runbooks("cannot sign in", tenant_id=999), indent=2))

    print("\n--- search_runbooks: empty query ---")
    print(json.dumps(search_runbooks("   ", tenant_id=1), indent=2))

    print("\n--- search_runbooks: too long ---")
    print(json.dumps(search_runbooks("x" * 600, tenant_id=1), indent=2))