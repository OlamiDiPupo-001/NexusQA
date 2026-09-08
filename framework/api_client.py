"""
A thin wrapper around httpx for making requests to the backend under test.

Why wrap httpx instead of calling it directly from every test? Centralizing
this means: if the backend later requires an auth header on every request,
you add it here once — not in every single test file.
"""

import httpx

from framework.config import settings


class ApiClient:
    def __init__(self, base_url: str | None = None, timeout: float | None = None):
        self.base_url = base_url or settings.backend_url
        self.timeout = timeout or settings.default_timeout
        self._client = httpx.Client(base_url=self.base_url, timeout=self.timeout)

    def get(self, path: str, **kwargs) -> httpx.Response:
        return self._client.get(path, **kwargs)

    def post(self, path: str, **kwargs) -> httpx.Response:
        return self._client.post(path, **kwargs)

    def close(self) -> None:
        self._client.close()
