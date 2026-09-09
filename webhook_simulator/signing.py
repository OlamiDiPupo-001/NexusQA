"""
Shared HMAC-SHA256 signing/verification logic. Imported by BOTH the
webhook simulator (to sign outgoing events) and the backend's webhook
route (to verify incoming ones). One implementation, two consumers —
this is deliberate, per the Phase 3 decision to avoid duplicating
signature logic in two places where it could silently drift apart.
"""

import hashlib
import hmac
import json


def sign_payload(payload: dict, secret: str) -> str:
    """
    Produces a signature over the payload's exact JSON representation.
    sort_keys=True matters: it guarantees the same dict always serializes
    to the same string, regardless of insertion order, so signing and
    verifying always hash identical bytes for identical data.
    """
    message = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()


def verify_signature(payload: dict, signature: str, secret: str) -> bool:
    expected = sign_payload(payload, secret)
    return hmac.compare_digest(expected, signature)
