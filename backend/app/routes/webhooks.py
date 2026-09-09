"""
Real webhook handling logic: verify authenticity (HMAC), then check
idempotency (event_id), THEN process. Order matters — see Phase 7 notes
on why the idempotency check must short-circuit as early as possible.
"""

import asyncio
import time

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

_request_timestamps: list[float] = []
_RATE_LIMIT = 3  # max requests allowed
_RATE_WINDOW = 2.0  # per this many seconds

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


@router.post("/webhooks/rate-limited-endpoint")
def rate_limited_endpoint():
    """
    Deliberately simple fixed-window rate limiter, existing purely to
    give the Tenacity retry test something real to back off against.
    Not a production-grade rate limiter — no need for one here.
    """
    now = time.monotonic()
    _request_timestamps[:] = [t for t in _request_timestamps if now - t < _RATE_WINDOW]

    if len(_request_timestamps) >= _RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    _request_timestamps.append(now)
    return {"ok": True}


@router.post("/webhooks/slow-endpoint")
async def slow_endpoint():
    """Deliberately slow response, purely to test client-side timeout
    behavior — does the client fail fast and predictably, or hang?"""
    await asyncio.sleep(3)
    return {"ok": True}
