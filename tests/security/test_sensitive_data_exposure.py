"""
Proves card data never appears in plaintext in logs. Run this BEFORE
the sanitize_for_logging fix below — it should FAIL, since the current
webhook route logs the raw, unmasked payload.
"""

import logging

from framework.config import settings
from webhook_simulator.signing import sign_payload


def test_card_number_never_appears_unmasked_in_logs(client, caplog):
    # Stripe's published test card number — never a real card, per
    # Section 2K's test-data strategy, but exactly the kind of value
    # that should never leak into logs regardless.
    payload = {
        "event_id": "evt_card_test",
        "order_id": 1,
        "card_number": "4242424242424242",
    }
    signature = sign_payload(payload, settings.webhook_secret)

    with caplog.at_level(logging.INFO):
        client.post(
            "/webhooks/payment",
            json=payload,
            headers={"X-Webhook-Signature": signature},
        )

    full_log_output = caplog.text
    assert "4242424242424242" not in full_log_output, (
        "Full card number appeared in plaintext in application logs — "
        "this is a sensitive data exposure vulnerability."
    )


def test_invalid_signature_error_does_not_leak_internals(client):
    """
    Proves a rejected webhook's error response doesn't accidentally
    include the payload, the expected signature, or other internal
    detail an attacker could use to refine their next attempt.
    """
    response = client.post(
        "/webhooks/payment",
        json={"event_id": "evt_x", "order_id": 1, "card_number": "4242424242424242"},
        headers={"X-Webhook-Signature": "wrong-signature"},
    )
    body = response.text
    assert "4242424242424242" not in body
    assert settings.webhook_secret not in body
