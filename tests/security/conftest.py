import pytest
from fastapi.testclient import TestClient

from backend.app.db import Base, engine
from backend.app.main import app
from backend.app.routes.webhooks import reset_signature_lockout_state


@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def _reset_webhook_rate_limit_state():
    """Runs automatically before EVERY test in this folder — no test
    needs to request it by name. Prevents lockout state from one test
    silently affecting the next."""
    reset_signature_lockout_state()
    yield
