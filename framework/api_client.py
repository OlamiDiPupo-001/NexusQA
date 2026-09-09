"""
A thin wrapper around httpx for making requests to the backend under test.

Why wrap httpx instead of calling it directly from every test? Centralizing
this means: if the backend later requires an auth header on every request,
you add it here once — not in every single test file.
"""

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

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

    @retry(
        retry=retry_if_exception_type(httpx.HTTPStatusError),
        stop=stop_after_attempt(5),
        wait=wait_exponential(min=0.5, max=4),
        reraise=True,
    )
    def post_with_retry(self, path: str, **kwargs) -> httpx.Response:
        """
        POSTs with automatic retry+backoff on any HTTP error status
        (including 429). reraise=True means if ALL attempts are
        exhausted, the real underlying error is raised — not a generic
        Tenacity wrapper exception — so test failures stay readable.
        """
        response = self._client.post(path, **kwargs)
        response.raise_for_status()
        return response
