"""Shared fixtures for the Social Mirror QA test suite."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client():
    """FastAPI TestClient for endpoint tests."""
    return TestClient(app)
