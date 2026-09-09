"""
Proves (or disproves) that concurrent checkout requests against limited
stock can oversell. Run this BEFORE the atomic-update fix below — it
should FAIL, demonstrating the race condition genuinely exists.
"""

import asyncio

import httpx

from backend.app.db import seed_stock


async def test_concurrent_checkout_does_not_oversell(chaos_server):
    seed_stock(quantity=3)

    async with httpx.AsyncClient(base_url=chaos_server) as client:
        responses = await asyncio.gather(*[client.post("/checkout/limited") for _ in range(5)])

    successes = [r for r in responses if r.status_code == 200]
    assert len(successes) == 3, (
        f"Expected exactly 3 successful checkouts against a stock of 3, "
        f"got {len(successes)} — this indicates a race condition allowed "
        f"overselling."
    )
