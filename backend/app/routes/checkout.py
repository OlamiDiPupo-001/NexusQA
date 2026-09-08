"""
Checkout: turns a cart into a pending Order record. This is the endpoint
Layer 3's concurrency tests will hammer with simultaneous requests later,
so its current simplicity (no locking, no idempotency key) is deliberate —
it's the honest baseline those tests are designed to stress.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.db import OrderRecord, get_db
from backend.app.routes.cart import get_cart_total

router = APIRouter()


class CheckoutRequest(BaseModel):
    session_id: str


@router.post("/checkout")
def checkout(request: CheckoutRequest, db: Session = Depends(get_db)):
    total = get_cart_total(request.session_id)
    order = OrderRecord(total_cents=total, status="pending", created_at=datetime.now(UTC))
    db.add(order)
    db.commit()
    db.refresh(order)
    return {"order_id": order.id, "total_cents": order.total_cents, "status": order.status}
