"""
Root-level fixtures shared across ALL test layers (functional, chaos,
security). Keep this file small on purpose — anything specific to one
layer belongs in that layer's own conftest.py instead
"""

import pytest

from framework.api_client import ApiClient


@pytest.fixture
def api_client():
    """
    Provides a fresh ApiClient to any test that requests it by name.
    'yield' instead of 'return' means we can clean up (close the client)
    after the test finishes, even if the test fails.
    """
    client = ApiClient()
    yield client
    client.close()
