"""
Proves malformed webhook input is rejected gracefully (400) rather than
crashing the handler (500). Relies on the input validation you added to
webhooks.py back in Phase 7 Part A.
"""

from webhook_simulator.simulator import send_malformed_webhook


def test_malformed_webhook_returns_400_not_500(chaos_server):
    response = send_malformed_webhook(chaos_server)
    assert response.status_code == 400, (
        f"Expected a graceful 400 rejection, got {response.status_code} — "
        f"a 500 here would mean malformed input crashes the handler "
        f"instead of being validated."
    )
