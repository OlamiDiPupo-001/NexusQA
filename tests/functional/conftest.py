"""
Fixtures specific to functional tests only — not shared with chaos or
security layers, per the scoped-conftest reasoning from Phase 3.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.db import Base, engine
from backend.app.main import app


@pytest.fixture
def client():
    """Fresh DB schema + FastAPI TestClient per test, so tests never
    leak state into each other."""
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)
