"""
DELIBERATELY VULNERABLE endpoint — builds SQL via raw string
interpolation instead of a parameterized query, existing purely to give
the SQL injection test below a real bug to catch. Fixed later in this
same phase.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.db import get_db

router = APIRouter()

"""    (expect it to FAIL)
@router.get("/stock/search")
def search_stock(item_name: str, db: Session = Depends(get_db)):
    query = f"SELECT id, item_name, quantity FROM stock WHERE item_name = '{item_name}'"
    result = db.execute(text(query))
    rows = result.fetchall()
    return [{"id": r[0], "item_name": r[1], "quantity": r[2]} for r in rows]
"""


@router.get("/stock/search")
def search_stock(item_name: str, db: Session = Depends(get_db)):
    result = db.execute(
        text("SELECT id, item_name, quantity FROM stock WHERE item_name = :name"),
        {"name": item_name},
    )
    rows = result.fetchall()
    return [{"id": r[0], "item_name": r[1], "quantity": r[2]} for r in rows]
