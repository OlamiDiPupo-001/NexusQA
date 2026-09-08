"""
Pydantic models for NexusQA's Order & Payment Lifecycle.

These models are the single source of truth for what a valid Order or
WebhookEvent looks like. Both the backend app and the test suite import
from here — so a test can never accidentally expect a shape of data that
the backend doesn't actually produce, and vice versa. This is the core
mechanic behind "contract testing" (you'll build the actual contract tests
in Phase 6).
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class OrderStatus(StrEnum):
    """
    An Order can only ever be in one of these states. Using an Enum instead
    of a plain string ('pending', 'paid', etc.) means a typo like 'payed'
    is caught immediately by Python itself, not silently accepted as a new,
    unintended status.
    """

    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"


class Order(BaseModel):
    id: int
    total_cents: int = Field(
        gt=0, description="Total price in cents, never dollars — avoids float rounding bugs"
    )
    status: OrderStatus
    created_at: datetime


class WebhookEvent(BaseModel):
    """
    Represents an incoming payment webhook event, before it's been verified
    or processed. 'event_id' is the field idempotency checks key off
    """

    event_id: str
    order_id: int
    payload: dict
    signature: str
