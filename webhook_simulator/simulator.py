"""
Controllable fake payment-provider webhook sender. Supports normal
sends plus the specific misbehaviors chaos tests need: duplicate
delivery, tampered payloads, and (in Part B) delay injection.
"""

import uuid

import httpx

from framework.config import settings
from webhook_simulator.signing import sign_payload


def build_event(order_id: int, event_id: str | None = None) -> dict:
    """Builds a single webhook event payload. event_id is auto-generated
    unless explicitly passed — passing the SAME event_id twice is exactly
    how tests simulate a duplicate delivery."""
    return {
        "event_id": event_id or str(uuid.uuid4()),
        "order_id": order_id,
    }


def send_webhook(
    base_url: str,
    payload: dict,
    tamper: bool = False,
) -> httpx.Response:
    """
    Sends a single signed webhook. If tamper=True, the signature is
    computed over the ORIGINAL payload but a modified payload is sent —
    simulating an attacker altering data in transit after signing.
    """
    signature = sign_payload(payload, settings.webhook_secret)

    if tamper:
        payload = {**payload, "order_id": payload["order_id"] + 9999}

    return httpx.post(
        f"{base_url}/webhooks/payment",
        json=payload,
        headers={"X-Webhook-Signature": signature},
    )
