import os

os.environ.setdefault("ENVIRONMENT", "test")
# Unreachable DB on purpose: unit tests must not require PostgreSQL.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import pytest  # noqa: E402
from app.main import app  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
