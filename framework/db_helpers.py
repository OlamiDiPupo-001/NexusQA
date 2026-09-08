"""
Direct SQL query helpers — used to verify data actually persisted
correctly, independent of what the API claims. This matters because a
test that only checks the API's response has proven the API SAID it
worked, not that it actually did.
"""

from sqlalchemy import text
from sqlalchemy.orm import Session


def count_orders_with_status(db: Session, status: str) -> int:
    result = db.execute(
        text("SELECT COUNT(*) FROM orders WHERE status = :status"),
        {"status": status},
    )
    return result.scalar()
