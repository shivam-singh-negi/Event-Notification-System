import time


def test_event_status_initially_pending(client):
    response = client.post(
        "/api/events",
        json={
            "eventType": "EMAIL",
            "payload": {
                "recipient": "test@example.com",
                "message": "Hello"
            },
            "callbackUrl": "http://example.com/callback"
        },
    )

    event_id = response.json()["eventId"]

    status_resp = client.get(f"/api/events/{event_id}/status")

    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "PENDING"

def test_event_status_unknown_event_returns_404(client):
    response = client.get("/api/events/unknown-event-id/status")

    assert response.status_code == 404
    assert response.json()["detail"] == "Event not found"


def test_event_status_is_idempotent(client):
    response = client.post(
        "/api/events",
        json={
            "eventType": "EMAIL",
            "payload": {
                "recipient": "test@example.com",
                "message": "Hello"
            },
            "callbackUrl": "http://example.com/callback"
        },
    )

    event_id = response.json()["eventId"]

    for _ in range(3):
        status_resp = client.get(f"/api/events/{event_id}/status")
        assert status_resp.status_code == 200
        assert status_resp.json()["status"] == "PENDING"

def test_event_status_response_schema(client):
    response = client.post(
        "/api/events",
        json={
            "eventType": "EMAIL",
            "payload": {
                "recipient": "test@example.com",
                "message": "Hello"
            },
            "callbackUrl": "http://example.com/callback"
        },
    )

    event_id = response.json()["eventId"]

    status_resp = client.get(f"/api/events/{event_id}/status")
    body = status_resp.json()

    assert set(body.keys()) == {"eventId", "status"}
    assert body["eventId"] == event_id

def test_multiple_events_have_independent_status(client):
    r1 = client.post(
        "/api/events",
        json={
            "eventType": "EMAIL",
            "payload": {
                "recipient": "a@example.com",
                "message": "Hello"
            },
            "callbackUrl": "http://example.com/callback"
        },
    )

    r2 = client.post(
        "/api/events",
        json={
            "eventType": "EMAIL",
            "payload": {
                "recipient": "b@example.com",
                "message": "Hello"
            },
            "callbackUrl": "http://example.com/callback"
        },
    )

    id1 = r1.json()["eventId"]
    id2 = r2.json()["eventId"]

    assert client.get(f"/api/events/{id1}/status").json()["status"] == "PENDING"
    assert client.get(f"/api/events/{id2}/status").json()["status"] == "PENDING"

def test_event_status_invalid_id_format(client):
    response = client.get("/api/events/!!!/status")

    assert response.status_code == 404
