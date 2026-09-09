"""
Layer 2 — UI test, using Playwright + the Page Object Model.
Reserved for things that genuinely require a browser; everything else
(as in Step 9) goes through the API directly, which is faster and less
brittle.
"""

import subprocess
import time

import pytest

from framework.pom.checkout_page import CheckoutPage


@pytest.fixture(scope="module")
def live_server():
    """
    Playwright needs a REAL running server (not TestClient) since it's
    driving an actual browser making real network requests.
    """
    proc = subprocess.Popen(["uvicorn", "backend.app.main:app", "--port", "8001"])
    time.sleep(2)  # crude wait for startup — replaced with a health-check poll later
    yield "http://localhost:8001"
    proc.terminate()


def test_checkout_page_confirms_payment(page, live_server):
    checkout = CheckoutPage(page)
    checkout.goto(live_server)
    checkout.pay()
    assert checkout.is_confirmed()
