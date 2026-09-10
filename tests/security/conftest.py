import pytest
from fastapi.testclient import TestClient

from backend.app.db import Base, engine
from backend.app.main import app


@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)
