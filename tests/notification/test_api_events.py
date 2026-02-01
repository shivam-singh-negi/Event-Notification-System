import pytest
from app.notification.models import EventType


# ------------------------------------------------------------------
# Happy paths
# ------------------------------------------------------------------

@pytest.mark.parametrize(
    "event_type,payload",
    [
        (
            "EMAIL",
            {"recipient": "user@example.com", "message": "Hello"},
        ),
        (
            "SMS",
            {"phoneNumber": "+1234567890", "message": "Hello"},
        ),
        (
            "PUSH",
            {"deviceId": "device-123", "message": "Hello"},
        ),
    ],
)
def test_create_event_success(client, event_type, payload):
    response = client.post(
        "/api/events",
        json={
            "eventType": event_type,
            "payload": payload,
            "callbackUrl": "http://example.com/callback",
        },
    )

    assert response.status_code == 202
    assert isinstance(response.json()["eventId"], str)


# ------------------------------------------------------------------
# Missing required fields
# ------------------------------------------------------------------

@pytest.mark.parametrize(
    "event_type,payload,missing_field",
    [
        ("EMAIL", {"message": "Hello"}, "recipient"),
        ("SMS", {"message": "Hello"}, "phoneNumber"),
        ("PUSH", {"message": "Hello"}, "deviceId"),
    ],
)
def test_create_event_missing_required_fields(
    client, event_type, payload, missing_field
):
    response = client.post(
        "/api/events",
        json={
            "eventType": event_type,
            "payload": payload,
            "callbackUrl": "http://example.com/callback",
        },
    )

    assert response.status_code == 422
    assert missing_field in response.text


# ------------------------------------------------------------------
# Extra / unsupported payload fields
# ------------------------------------------------------------------

@pytest.mark.parametrize(
    "event_type,payload,extra_field",
    [
        (
            "EMAIL",
            {"recipient": "a@b.com", "message": "Hello", "extra": "x"},
            "extra",
        ),
        (
            "SMS",
            {"phoneNumber": "+123", "message": "Hello", "recipient": "x"},
            "recipient",
        ),
        (
            "PUSH",
            {"deviceId": "d1", "message": "Hello", "phoneNumber": "x"},
            "phoneNumber",
        ),
    ],
)
def test_create_event_rejects_extra_payload_fields(
    client, event_type, payload, extra_field
):
    response = client.post(
        "/api/events",
        json={
            "eventType": event_type,
            "payload": payload,
            "callbackUrl": "http://example.com/callback",
        },
    )

    assert response.status_code == 422
    assert extra_field in response.text


# ------------------------------------------------------------------
# Invalid payload types
# ------------------------------------------------------------------

@pytest.mark.parametrize(
    "event_type,payload,field",
    [
        ("EMAIL", {"recipient": 123, "message": "Hello"}, "recipient"),
        ("SMS", {"phoneNumber": 9876543210, "message": "Hello"}, "phoneNumber"),
        ("PUSH", {"deviceId": ["not", "a", "string"], "message": "Hello"}, "deviceId"),
    ],
)
def test_create_event_invalid_payload_types(
    client, event_type, payload, field
):
    response = client.post(
        "/api/events",
        json={
            "eventType": event_type,
            "payload": payload,
            "callbackUrl": "http://example.com/callback",
        },
    )

    assert response.status_code == 422
    assert field in response.text
    assert "must be of type" in response.text


# ------------------------------------------------------------------
# Invalid event type
# ------------------------------------------------------------------

def test_create_event_unsupported_event_type(client):
    response = client.post(
        "/api/events",
        json={
            "eventType": "FAX",
            "payload": {"message": "Hello"},
            "callbackUrl": "http://example.com/callback",
        },
    )

    assert response.status_code == 422


# ------------------------------------------------------------------
# Invalid callback URL
# ------------------------------------------------------------------

def test_create_event_invalid_callback_url(client):
    response = client.post(
        "/api/events",
        json={
            "eventType": "EMAIL",
            "payload": {
                "recipient": "user@example.com",
                "message": "Hello",
            },
            "callbackUrl": "not-a-url",
        },
    )

    assert response.status_code == 422

def test_create_event_fails_during_shutdown(client):
    from app.main import shutdown_manager

    shutdown_manager.initiate_shutdown()

    response = client.post(
        "/api/events",
        json={
            "eventType": "EMAIL",
            "payload": {
                "recipient": "user@example.com",
                "message": "Hello",
            },
            "callbackUrl": "http://example.com/callback",
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Service is shutting down"


@pytest.mark.parametrize(
    "event_type,payload,queue_type",
    [
        ("EMAIL", {"recipient": "a@b.com", "message": "hi"}, EventType.EMAIL),
        ("SMS", {"phoneNumber": "+1234567890", "message": "hi"}, EventType.SMS),
        ("PUSH", {"deviceId": "device-1", "message": "hi"}, EventType.PUSH),
    ],
)
def test_event_assigned_to_correct_queue(
    client, event_type, payload, queue_type
):
    from app.notification.api import queue_manager

    before = queue_manager.size(queue_type)

    response = client.post(
        "/api/events",
        json={
            "eventType": event_type,
            "payload": payload,
            "callbackUrl": "http://example.com/callback",
        },
    )

    assert response.status_code == 202
    assert queue_manager.size(queue_type) == before + 1
