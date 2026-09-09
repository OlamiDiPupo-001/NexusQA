"""
Proves the backend correctly rejects unsigned/forged webhook events.
This is a 100%-bar test per Phase 1's success criteria — no tolerance
for false negatives here, unlike the probabilistic race-condition tests.
"""

from framework.config import settings
from webhook_simulator.signing import sign_payload


def test_valid_signature_is_accepted(client):
    payload = {"event_id": "evt_1", "order_id": 1}
    signature = sign_payload(payload, settings.webhook_secret)

    response = client.post(
        "/webhooks/payment",
        json=payload,
        headers={"X-Webhook-Signature": signature},
    )
    assert response.status_code == 200


def test_invalid_signature_is_rejected(client):
    payload = {"event_id": "evt_2", "order_id": 1}

    response = client.post(
        "/webhooks/payment",
        json=payload,
        headers={"X-Webhook-Signature": "not-a-real-signature"},
    )
    assert response.status_code == 401


def test_tampered_payload_is_rejected(client):
    """Signature is valid for the ORIGINAL payload, but the payload sent
    doesn't match it — simulating interception + tampering in transit."""
    original_payload = {"event_id": "evt_3", "order_id": 1}
    signature = sign_payload(original_payload, settings.webhook_secret)

    tampered_payload = {"event_id": "evt_3", "order_id": 999}

    response = client.post(
        "/webhooks/payment",
        json=tampered_payload,
        headers={"X-Webhook-Signature": signature},
    )
    assert response.status_code == 401
