"""
Fixtures specific to chaos/event-driven tests only.
"""

import subprocess
import time as time_module

import pytest
from fastapi.testclient import TestClient

from backend.app.db import Base, engine
from backend.app.main import app


@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def chaos_server():
    """A REAL running server, needed because true concurrency requires
    real simultaneous network requests — TestClient can't reliably
    recreate that."""
    proc = subprocess.Popen(["uvicorn", "backend.app.main:app", "--port", "8002"])
    time_module.sleep(2)
    yield "http://localhost:8002"
    proc.terminate()
