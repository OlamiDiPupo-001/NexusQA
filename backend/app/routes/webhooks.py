"""
Placeholder for now — deliberately NOT idempotent yet. Phase 7 is where
you'll add signature verification and the idempotency check against
ProcessedWebhookEvent. Leaving it naive here means Phase 7's tests have
a real bug to catch, then fix — that catch-then-fix moment is one of
your strongest interview demos.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.db import OrderRecord, get_db

router = APIRouter()


@router.post("/webhooks/payment")
def payment_webhook(payload: dict, db: Session = Depends(get_db)):
    order_id = payload.get("order_id")
    order = db.query(OrderRecord).filter(OrderRecord.id == order_id).first()
    if order:
        order.status = "paid"
        db.commit()
    return {"received": True}
