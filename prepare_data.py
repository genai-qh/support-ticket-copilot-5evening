from pathlib import Path
import duckdb

Path("data").mkdir(exist_ok=True)

with duckdb.connect() as db:
    db.execute("""
        CREATE TABLE tickets AS
        SELECT
            i AS ticket_id,
            1 + i % 2 AS tenant_id,
            CASE i % 3
                WHEN 0 THEN 'access'
                WHEN 1 THEN 'billing'
                ELSE 'reliability'
            END AS label,
            CASE i % 3
                WHEN 0 THEN 'Cannot sign in'
                WHEN 1 THEN 'Invoice total is wrong'
                ELSE 'API request timed out'
            END AS body
        FROM range(1, 121) AS t(i)
    """)

    db.execute("""
        COPY tickets TO 'data/tickets.parquet'
        (FORMAT PARQUET, COMPRESSION ZSTD)
    """)

    result = db.execute("""
        SELECT label, count(*)
        FROM 'data/tickets.parquet'
        GROUP BY label
        ORDER BY label
    """).fetchall()

    print(result)