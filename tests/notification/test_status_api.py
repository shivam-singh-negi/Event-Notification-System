from fastapi.testclient import TestClient


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def create_email_event(client: TestClient) -> str:
    response = client.post(
        "/api/events",
        json={
            "eventType": "EMAIL",
            "payload": {
                "recipient": "test@example.com",
                "message": "Hello",
            },
            "callbackUrl": "http://example.com/callback",
        },
    )
    assert response.status_code == 202
    return response.json()["eventId"]


# -------------------------------------------------------------------
# Core status behavior
# -------------------------------------------------------------------

def test_event_status_initially_pending(client: TestClient):
    """
    Newly created events must start in PENDING state.
    """
    event_id = create_email_event(client)

    response = client.get(f"/api/events/{event_id}/status")

    assert response.status_code == 200
    assert response.json()["status"] == "PENDING"


def test_event_status_unknown_event_returns_404(client: TestClient):
    """
    Querying an unknown event should return 404.
    """
    response = client.get("/api/events/non-existent-id/status")

    assert response.status_code == 404
    assert response.json()["detail"] == "Event not found"


def test_event_status_endpoint_is_idempotent(client: TestClient):
    """
    Multiple reads of the status endpoint should be safe and consistent.
    """
    event_id = create_email_event(client)

    for _ in range(3):
        response = client.get(f"/api/events/{event_id}/status")
        assert response.status_code == 200
        assert response.json()["status"] == "PENDING"


# -------------------------------------------------------------------
# API contract validation
# -------------------------------------------------------------------

def test_event_status_response_schema(client: TestClient):
    """
    Status response must follow the defined API contract.
    """
    event_id = create_email_event(client)

    response = client.get(f"/api/events/{event_id}/status")
    body = response.json()

    assert set(body.keys()) == {"eventId", "status"}
    assert body["eventId"] == event_id
    assert body["status"] == "PENDING"


def test_multiple_events_have_independent_status(client: TestClient):
    """
    Each event must maintain its own independent lifecycle state.
    """
    event_id_1 = create_email_event(client)
    event_id_2 = create_email_event(client)

    status_1 = client.get(f"/api/events/{event_id_1}/status").json()["status"]
    status_2 = client.get(f"/api/events/{event_id_2}/status").json()["status"]

    assert status_1 == "PENDING"
    assert status_2 == "PENDING"


def test_event_status_invalid_identifier_returns_404(client: TestClient):
    """
    Invalid path parameters should not crash the API.
    """
    response = client.get("/api/events/!!!/status")

    assert response.status_code == 404
