"""
Real webhook handling logic: verify authenticity (HMAC), then check
idempotency (event_id), THEN process. Order matters — see Phase 7 notes
on why the idempotency check must short-circuit as early as possible.
"""

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from backend.app.db import (
    OrderRecord,
    get_db,
    is_event_processed,
    mark_event_processed,
)
from framework.config import settings
from webhook_simulator.signing import verify_signature

router = APIRouter()


@router.post("/webhooks/payment")
def payment_webhook(
    payload: dict,
    db: Session = Depends(get_db),
    x_webhook_signature: str = Header(...),
):
    # 1. Verify authenticity FIRST — an unsigned/forged request should
    #    never reach idempotency or business logic at all.
    if not verify_signature(payload, x_webhook_signature, settings.webhook_secret):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    event_id = payload.get("event_id")
    order_id = payload.get("order_id")
    if not isinstance(event_id, str) or not isinstance(order_id, int):
        raise HTTPException(status_code=400, detail="Missing or invalid event_id/order_id")

    # 2. Idempotency check SECOND, before touching the order at all.
    #    A replayed, already-processed event does minimal work and exits.
    if is_event_processed(db, event_id):
        return {"received": True, "duplicate": True}

    # 3. Only now do we actually process the payment.
    order = db.query(OrderRecord).filter(OrderRecord.id == order_id).first()
    if order:
        order.status = "paid"
        db.commit()

    mark_event_processed(db, event_id, order_id)
    return {"received": True, "duplicate": False}
