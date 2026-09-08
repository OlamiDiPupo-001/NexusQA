"""
Central configuration for NexusQA.

Why this file exists: instead of hardcoding URLs or timeouts inside
individual test files, every test pulls its settings from here. This means
switching between "running locally against Docker Compose" and "running in
GitHub Actions CI" is a one-line environment variable change, not a
find-and-replace across dozens of files.
"""

import os


class Settings:
    # Base URL of the backend API. Defaults to local Docker Compose setup,
    # but CI can override this via an environment variable if the service
    # is reachable at a different address there.
    backend_url: str = os.getenv("NEXUSQA_BACKEND_URL", "http://localhost:8000")

    # Timeout (seconds) for HTTP requests made during tests. Kept centralized
    # so chaos tests can deliberately override it when testing slow responses.
    default_timeout: float = 5.0

    # Database connection string for direct SQL verification (Layer 2).
    db_url: str = os.getenv("NEXUSQA_DB_URL", "postgresql://nexusqa:nexusqa@localhost:5432/nexusqa")


settings = Settings()
