"""
Proves the client times out predictably against a slow endpoint,
rather than hanging indefinitely — a client with no timeout configured
is itself a resilience bug.
"""

import httpx
import pytest


@pytest.mark.flaky(
    reason="Tight timing margins caused flakiness"
    "challenges-and-solutions.md. 3s/1s margin resolved it."
)
def test_client_times_out_on_slow_response(chaos_server):
    with pytest.raises(httpx.TimeoutException):
        httpx.post(f"{chaos_server}/webhooks/slow-endpoint", timeout=1.0)
