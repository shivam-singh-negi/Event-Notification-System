import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# ------------------------------------------------------------------
# Ensure project root is on PYTHONPATH
# ------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from app.main import app, shutdown_manager  # noqa: E402


# ------------------------------------------------------------------
# Global test safety: reset shutdown state between tests
# ------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_shutdown_state():
    """
    Ensure the application is NOT in shutdown mode at the
    start of every test.

    Prevents global shutdown state from leaking across tests.
    """
    shutdown_manager.shutdown_event.clear()
    yield
    shutdown_manager.shutdown_event.clear()


# ------------------------------------------------------------------
# Test client
# ------------------------------------------------------------------

@pytest.fixture
def client():
    """
    FastAPI test client.
    """
    return TestClient(app)
