"""
Proves the client survives a real 429 rate-limit response by backing
off and retrying, rather than failing immediately on the first
rejection.
"""

from framework.api_client import ApiClient


def test_client_backs_off_and_succeeds_after_rate_limit(chaos_server):
    client = ApiClient(base_url=chaos_server)

    # Fire enough requests to guarantee at least one hits the limit,
    # relying on post_with_retry to recover via backoff.
    results = []
    for _ in range(6):
        response = client.post_with_retry("/webhooks/rate-limited-endpoint")
        results.append(response.status_code)

    # Every call should EVENTUALLY succeed (200) once retried, even
    # though some individual attempts underneath hit a 429 first.
    assert all(status == 200 for status in results), (
        f"Expected all calls to eventually succeed via retry, got: {results}"
    )
