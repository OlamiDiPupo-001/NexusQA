"""
Central place for redacting sensitive fields before anything gets
logged. All logging of payment/webhook payloads MUST go through this
function — never log a raw payload dict directly. Centralizing this in
one function (rather than masking inline at each log call) means a
missed field only needs fixing in one place.
"""

SENSITIVE_FIELDS = {"card_number", "cvv"}


def sanitize_for_logging(payload: dict) -> dict:
    sanitized = {}
    for key, value in payload.items():
        if key in SENSITIVE_FIELDS and isinstance(value, str) and len(value) >= 4:
            sanitized[key] = f"****{value[-4:]}"
        elif key in SENSITIVE_FIELDS:
            sanitized[key] = "****"
        else:
            sanitized[key] = value
    return sanitized
