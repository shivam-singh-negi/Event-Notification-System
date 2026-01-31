import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Resolve project root (Event-Notification-System/)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from app.main import app  # noqa: E402


@pytest.fixture
def client():
    return TestClient(app)
