from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.db import OrderRecord, get_db

router = APIRouter()


@router.get("/orders/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(OrderRecord).filter(OrderRecord.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return {
        "order_id": order.id,
        "total_cents": order.total_cents,
        "status": order.status,
        "created_at": order.created_at.isoformat(),
    }
