"""
Checkout: turns a cart into a pending Order record. This is the endpoint
Layer 3's concurrency tests will hammer with simultaneous requests later,
so its current simplicity (no locking, no idempotency key) is deliberate —
it's the honest baseline those tests are designed to stress.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
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


@router.post("/checkout/limited")
def checkout_limited_stock(db: Session = Depends(get_db)):
    """
    Atomic check-and-decrement: the database itself guarantees this
    happens as one indivisible step, so two concurrent requests can
    never both see stock as available when only one unit remains.
    """
    result = db.execute(
        text("UPDATE stock SET quantity = quantity - 1 WHERE item_name = :name AND quantity > 0"),
        {"name": "flash_sale_item"},
    )
    db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=409, detail="Out of stock")

    order = OrderRecord(total_cents=999, status="pending", created_at=datetime.now(UTC))
    db.add(order)
    db.commit()
    db.refresh(order)
    return {"order_id": order.id, "status": "purchased"}


'''
@router.post("/checkout/limited")
def checkout_limited_stock(db: Session = Depends(get_db)):
    """
    Deliberately naive read-then-write stock decrement. This EXISTS to
    give the concurrency test below a real bug to catch — do not model
    real checkout logic on this pattern. Fixed later in this same phase,
    once the race is proven to exist.
    """
    stock = db.query(StockRecord).filter_by(item_name="flash_sale_item").first()
    if not stock or stock.quantity <= 0:
        raise HTTPException(status_code=409, detail="Out of stock")

    current_quantity = stock.quantity
    time.sleep(0.05)  # artificially widens the race window so the bug
                       # shows up reliably in a test instead of only
                       # rarely, on unlucky timing
    stock.quantity = current_quantity - 1
    db.commit()

    order = OrderRecord(total_cents=999, status="pending", created_at=datetime.now(UTC))
    db.add(order)
    db.commit()
    db.refresh(order)
    return {"order_id": order.id, "status": "purchased"}
'''
