import duckdb

PARQUET = "data/tickets.parquet"

def _q(sql):
    with duckdb.connect() as db:
        return db.execute(sql).fetchall()

def test_row_count():
    assert _q(f"SELECT count(*) FROM '{PARQUET}'")[0][0] == 120

def test_unique_ticket_ids():
    dupes = _q(f"""
        SELECT ticket_id FROM '{PARQUET}'
        GROUP BY ticket_id HAVING count(*) > 1
    """)
    assert dupes == []

def test_required_columns():
    cols = {row[0] for row in _q(f"DESCRIBE SELECT * FROM '{PARQUET}'")}
    assert {"ticket_id", "tenant_id", "label", "body"} <= cols

def test_permitted_categories():
    labels = {row[0] for row in _q(f"SELECT DISTINCT label FROM '{PARQUET}'")}
    assert labels == {"access", "billing", "reliability"}

def test_tenant_ids():
    tenants = {row[0] for row in _q(f"SELECT DISTINCT tenant_id FROM '{PARQUET}'")}
    assert tenants == {1, 2}

def test_each_category_has_40():
    rows = dict(_q(f"SELECT label, count(*) FROM '{PARQUET}' GROUP BY label"))
    assert rows == {"access": 40, "billing": 40, "reliability": 40}