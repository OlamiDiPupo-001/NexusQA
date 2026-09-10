"""
Proves the stock search endpoint isn't vulnerable to SQL injection.
Run this BEFORE the parameterized-query fix below — it should FAIL,
proving the injection genuinely works against the naive implementation.
"""

from backend.app.db import seed_stock


def test_sql_injection_cannot_bypass_where_clause(client):
    seed_stock(quantity=5)  # creates exactly one real stock row

    malicious_input = "nonexistent' OR '1'='1"
    response = client.get("/stock/search", params={"item_name": malicious_input})
    data = response.json()

    assert len(data) == 0, (
        f"Searching for a nonexistent item should return 0 rows, but got "
        f"{len(data)} — the OR '1'='1' injection bypassed the WHERE "
        f"clause and returned every row in the table instead of none."
    )
