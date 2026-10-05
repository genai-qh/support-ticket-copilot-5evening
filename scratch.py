import duckdb

with duckdb.connect() as db:
    print("=== DESCRIBE ===")
    print(db.execute("DESCRIBE SELECT * FROM 'data/tickets.parquet'").fetchall())

    print("\n=== EXPLAIN (tenant-filtered) ===")
    plan = db.execute("""
        EXPLAIN
        SELECT ticket_id, label
        FROM 'data/tickets.parquet'
        WHERE tenant_id = 1
    """).fetchall()
    for row in plan:
        print(row[1])