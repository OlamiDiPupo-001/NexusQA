"""
Proves repeated invalid signature attempts trigger lockout (429),
protecting the signature check from brute-force guessing — while
confirming legitimate, correctly-signed requests are never penalized.
"""

from framework.config import settings
from webhook_simulator.signing import sign_payload


def test_repeated_invalid_signatures_trigger_lockout(client):
    bad_payload = {"event_id": "evt_bruteforce", "order_id": 1}

    # First 3 failed attempts — these establish the failure count.
    for _ in range(3):
        response = client.post(
            "/webhooks/payment",
            json=bad_payload,
            headers={"X-Webhook-Signature": "wrong"},
        )
        assert response.status_code == 401

    # 4th attempt should be locked out, even with a WRONG signature —
    # the lockout itself is now the reason for rejection, not the
    # signature check reaching a verdict.
    locked_response = client.post(
        "/webhooks/payment",
        json=bad_payload,
        headers={"X-Webhook-Signature": "wrong"},
    )
    assert locked_response.status_code == 429


def test_legitimate_requests_are_never_penalized(client):
    """A run of genuinely valid, correctly-signed requests should never
    trigger lockout, since only FAILURES count against the limit."""
    for i in range(5):
        payload = {"event_id": f"evt_legit_{i}", "order_id": 1}
        signature = sign_payload(payload, settings.webhook_secret)
        response = client.post(
            "/webhooks/payment",
            json=payload,
            headers={"X-Webhook-Signature": signature},
        )
        assert response.status_code == 200
