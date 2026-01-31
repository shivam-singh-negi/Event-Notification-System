def test_create_event_success(client):
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

    assert response.status_code == 202
    body = response.json()
    assert "eventId" in body


def test_create_event_invalid_payload(client):
    response = client.post(
        "/api/events",
        json={
            "eventType": "EMAIL",
            "payload": {"message": "Hello"},
            "callbackUrl": "http://example.com/callback"
        },
    )

    assert response.status_code == 422

def test_create_event_unsupported_event_type(client):
    response = client.post(
        "/api/events",
        json={
            "eventType": "FAX",
            "payload": {
                "recipient": "test@example.com",
                "message": "Hello"
            },
            "callbackUrl": "http://example.com/callback"
        },
    )

    assert response.status_code == 422


def test_create_sms_event_missing_phone_number(client):
    response = client.post(
        "/api/events",
        json={
            "eventType": "SMS",
            "payload": {
                "message": "Hello"
            },
            "callbackUrl": "http://example.com/callback"
        },
    )

    assert response.status_code == 422


def test_create_event_invalid_callback_url(client):
    response = client.post(
        "/api/events",
        json={
            "eventType": "EMAIL",
            "payload": {
                "recipient": "test@example.com",
                "message": "Hello"
            },
            "callbackUrl": "not-a-url"
        },
    )

    assert response.status_code == 422


def test_create_event_empty_payload(client):
    response = client.post(
        "/api/events",
        json={
            "eventType": "EMAIL",
            "payload": {},
            "callbackUrl": "http://example.com/callback"
        },
    )

    assert response.status_code == 422


def test_create_event_payload_not_object(client):
    response = client.post(
        "/api/events",
        json={
            "eventType": "EMAIL",
            "payload": "hello",
            "callbackUrl": "http://example.com/callback"
        },
    )

    assert response.status_code == 422


def test_create_sms_event_success(client):
    response = client.post(
        "/api/events",
        json={
            "eventType": "SMS",
            "payload": {
                "phoneNumber": "+1234567890",
                "message": "Hello"
            },
            "callbackUrl": "http://example.com/callback"
        },
    )

    assert response.status_code == 202
    assert "eventId" in response.json()


def test_create_push_event_success(client):
    response = client.post(
        "/api/events",
        json={
            "eventType": "PUSH",
            "payload": {
                "deviceId": "device-123",
                "message": "Hello"
            },
            "callbackUrl": "http://example.com/callback"
        },
    )

    assert response.status_code == 202
    assert "eventId" in response.json()
